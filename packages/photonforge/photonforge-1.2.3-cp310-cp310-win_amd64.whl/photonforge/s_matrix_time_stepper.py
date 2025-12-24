import threading
import time
import warnings
from collections.abc import Sequence
from typing import Any, Literal

import numpy

from .cache import _pole_residue_fit_cache
from .extension import (
    Component,
    PoleResidueMatrix,
    SMatrix,
    TimeDomainModel,
    TimeStepper,
    _content_repr,
    config,
    frequency_classification,
    pole_residue_fit,
    register_time_stepper_class,
)
from .typing import Frequency, NonNegativeInt, PositiveFloat, PositiveInt, TimeDelay


class SMatrixTimeStepper(TimeStepper):
    """Time stepper based on a time-domain model.

    The :class:`TimeDomainModel` can be calculated automatically using
    :func:`pole_residue_fit` and the component's S matrix or from the
    provided :class:`PoleResidueMatrix`.

    Args:
        pole_residue_matrix: Pole-residue matrix for the underlying
          time-domain model. If provided, all other arguments are not used.
        s_matrix_kwargs: Keyword arguments for :func:`Component.s_matrix`.
        initial_poles: Sequence of poles used as initial guess.
        min_poles: Minimal number of poles to try. It has no effect when
          initial pole guesses are provided.
        max_poles: Maximal number of poles to try. It has no effect when
          initial pole guesses are provided.
        loss_factor: For complex initial pole guesses, ratio between their
          real and imaginary parts.
        rms_error_tolerance: RMS error level to break the fitting loop.
        max_iterations: Maximal number of fitting iterations.
        max_stale_iterations: Maximal number of iterations without error
          progress.
        passive: Whether to attempt to enforce passivity.
        feedthrough: Whether to include a feedthrough (constant) term in the
          pole-residue model.
        delays: Time delays (in seconds), one per matrix element. Missing
          elements have no time delay applied. If a single number is given,
          this is used as a global delay for all matrix elements. If
          ``"auto"``, the delays are estimated from the provided data.
    """

    def __init__(
        self,
        pole_residue_matrix: PoleResidueMatrix | None = None,
        s_matrix_kwargs: dict[str, Any] = {},
        initial_poles: Sequence[complex] = (),
        min_poles: NonNegativeInt = 0,
        max_poles: NonNegativeInt = 6,
        loss_factor: PositiveFloat = 1e-3,
        rms_error_tolerance: PositiveFloat = 1e-4,
        max_iterations: PositiveInt = 100,
        max_stale_iterations: PositiveInt = 3,
        passive: bool = True,
        feedthrough: bool | None = None,
        delays: Literal["auto"] | TimeDelay | dict[tuple[str, str], TimeDelay] = "auto",
    ) -> None:
        super().__init__(
            pole_residue_matrix=pole_residue_matrix,
            s_matrix_kwargs=s_matrix_kwargs,
            initial_poles=initial_poles,
            min_poles=min_poles,
            max_poles=max_poles,
            loss_factor=loss_factor,
            rms_error_tolerance=rms_error_tolerance,
            max_iterations=max_iterations,
            max_stale_iterations=max_stale_iterations,
            passive=passive,
            feedthrough=feedthrough,
            delays=delays,
        )

    def setup_state(
        self,
        *,
        component: Component,
        time_step: float,
        carrier_frequency: float,
        frequencies: Sequence[Frequency] = (),
        **kwargs,
    ):
        """Initialize internal state, building a time domain model if necessary.

        Args:
            component: Component for the time stepper.
            time_step: The interval between time steps (in seconds).
            carrier_frequency: The carrier frequency used to construct the time
              stepper. The carrier should be omitted from the input signals, as
              it is handled automatically by the time stepper.
            frequencies: Frequencies used to build the S matrix for
              ``component``, if a ``pole_residue_matrix`` is not provided.
            kwargs: Unused.
        """
        self._thread = None
        self.s_matrix = None
        self.rms_error = None
        self.fit_kwargs = None
        self.time_domain_model = None

        pole_residue = self.parametric_kwargs["pole_residue_matrix"]

        if pole_residue is not None:
            self.time_domain_model = TimeDomainModel(pole_residue, time_step)
            return None

        try:
            self._cache_key = _content_repr(
                self, component, time_step, carrier_frequency, frequencies, kwargs
            )
            cached_values = _pole_residue_fit_cache[self._cache_key]
        except Exception:
            warnings.warn(
                f"Unable to cache pole-residue fit results for component '{component.name}'.",
                RuntimeWarning,
                2,
            )

        if cached_values is not None:
            s_matrix, fit_kwargs, rms_error, pole_residue = cached_values
            # We don't want to expose the cached data to the user: use a copies
            self.s_matrix = s_matrix.copy()
            self.rms_error = rms_error
            self.fit_kwargs = dict(fit_kwargs)
            self.time_domain_model = TimeDomainModel(pole_residue.copy(), time_step)
            return None

        if len(frequencies) == 0:
            raise RuntimeError(
                f"Argument 'frequencies' must be provided for S matrix computation for "
                f"component '{component.name}."
            )

        # Start S matrix computation (we cannot use 'component' after returning, because it might
        # get updated and it will affect our running thread.
        classification = frequency_classification(frequencies)
        model = component.select_active_model(classification)
        if model is None:
            raise RuntimeError(f"No active {classification} model in component '{component.name}'.")

        s_matrix_kwargs = self.parametric_kwargs["s_matrix_kwargs"]
        s_matrix_kwargs["verbose"] = False
        s_matrix_runner = model.start(component, frequencies, **s_matrix_kwargs)

        self._lock = threading.Lock()
        self._status = {"progress": 0, "message": "running"}
        self._thread = threading.Thread(
            daemon=True,
            target=self._fit_s_matrix,
            args=(component.name, s_matrix_runner, carrier_frequency, time_step),
        )
        self._thread.start()
        return self

    def reset(self):
        """Reset the state of the internal time domain model."""
        self.time_domain_model.reset()

    def step_single(
        self, inputs: dict[str, complex], time_index: int, update_state: bool, shutdown: bool
    ) -> dict[str, complex]:
        """Take a single time step on the given inputs.

        Args:
            inputs: Dictionary containing inputs at the current time step,
              mapping port names to complex values.
            time_index: Time series index for the current input.
            update_state: Whether to update the internal stepper state.
            shutdown: Whether this is the last call to the single stepping
              function for the provided :class:`TimeSeries`.

        Returns:
            Outputs at the current time step.
        """
        return self.time_domain_model.step(inputs=inputs, update_state=update_state)

    @property
    def status(self):
        if not self._thread.is_alive() and self._status["message"] == "running":
            self._status["message"] = "error"
        with self._lock:
            return self._status

    def _fit_s_matrix(self, component_name, s_matrix_runner, carrier_frequency, time_step):
        if isinstance(s_matrix_runner, SMatrix):
            self.s_matrix = s_matrix_runner
            with self._lock:
                self._status = {"message": "running", "progress": 50}
        else:
            while True:
                status = dict(s_matrix_runner.status)
                message = status.pop("message")
                status["progress"] *= 0.5
                with self._lock:
                    self._status = {"message": "running", **status}
                if message != "running":
                    break
                time.sleep(0.3)

            if message == "error":
                with self._lock:
                    self._status["message"] = "error"
                return

            self.s_matrix = s_matrix_runner.s_matrix

        frequencies_shifted = self.s_matrix.frequencies - carrier_frequency
        s_matrix_shifted = SMatrix(
            frequencies=frequencies_shifted,
            elements=self.s_matrix.elements,
            ports=self.s_matrix.ports,
        )

        # Setup pole_residue_fit kwargs
        fit_kwargs = dict(self.parametric_kwargs)
        fit_kwargs.pop("s_matrix_kwargs")
        fit_kwargs.pop("pole_residue_matrix")
        fit_kwargs.update(
            {"stable": True, "silence_warnings": True, "real": carrier_frequency == 0}
        )

        passive = fit_kwargs.pop("passive")
        if passive:
            freqs = self.s_matrix.frequencies
            elements = self.s_matrix.elements
            input_keys = {k for k, _ in elements.keys()}
            output_keys = {k for _, k in elements.keys()}
            s_flat = numpy.zeros((len(freqs), len(output_keys), len(input_keys)), dtype=complex)
            for j, input_key in enumerate(input_keys):
                for i, output_key in enumerate(output_keys):
                    s_entry = elements.get((input_key, output_key))
                    if s_entry is not None:
                        s_flat[:, i, j] = s_entry

            singvals = numpy.linalg.svd(s_flat, compute_uv=False)
            if numpy.any(singvals > 1.01):
                warnings.warn(
                    f"S matrix is not passive for '{component_name}'. Largest singular value is "
                    f"'{singvals.max():.4f}'.",
                    RuntimeWarning,
                    2,
                )

        delays = fit_kwargs.pop("delays")
        if delays == "auto":
            # Try some delay scales. Quantize delays in terms of time step.
            delays = s_matrix_shifted.estimate_delays(lossless=True)
            delays_list = [
                {key: int(scale * val / time_step) * time_step for key, val in delays.items()}
                for scale in [0, 0.8, 1]
            ]
        else:
            delays_list = [delays]

        feedthrough = fit_kwargs.pop("feedthrough")
        feedthrough_list = [True, False] if feedthrough is None else [feedthrough]

        min_poles = fit_kwargs.pop("min_poles")
        max_poles = fit_kwargs.pop("max_poles")

        kwargs_list = [
            {
                "delays": delays,
                "feedthrough": feedthrough,
                "min_poles": num_poles,
                "max_poles": num_poles,
                **fit_kwargs,
            }
            for num_poles in range(min_poles, max_poles + 1)
            for delays in delays_list
            for feedthrough in feedthrough_list
        ]

        # Pole-residue fit
        fit_progress = 0
        fit_progress_total = sum((1 + kwargs["max_poles"] ** 3) for kwargs in kwargs_list)
        rms_error_tolerance = fit_kwargs["rms_error_tolerance"]

        best_non_passive_err = None
        best_passive_err = None
        for kwargs in kwargs_list:
            fit_progress += 1 + kwargs["max_poles"] ** 3
            with self._lock:
                self._status = {
                    "message": "running",
                    "progress": 50 + 50 * fit_progress / fit_progress_total,
                }

            pole_residue, err = pole_residue_fit(s_matrix_shifted, passive=False, **kwargs)

            if best_non_passive_err is None or err < best_non_passive_err:
                best_non_passive_err = err
                best_non_passive_pr = pole_residue
                best_non_passive_kwargs = fit_kwargs

            if passive:
                is_passive = pole_residue.is_passive()
                if is_passive:
                    passive_err = err
                elif (
                    best_passive_err is None or err < best_passive_err
                ) and pole_residue.enforce_passivity(
                    frequencies=s_matrix_shifted.frequencies,
                    feedthrough=kwargs["feedthrough"],
                    real=kwargs["real"],
                ):
                    is_passive = True
                    passive_err = pole_residue.get_rms_error(s_matrix_shifted)
                if is_passive and (best_passive_err is None or passive_err <= best_passive_err):
                    best_passive_err = passive_err
                    best_passive_pr = pole_residue
                    best_passive_kwargs = fit_kwargs
                    if best_passive_err <= rms_error_tolerance:
                        break
            elif best_non_passive_err is not None and best_non_passive_err <= rms_error_tolerance:
                break

        if best_passive_err is not None:
            pole_residue = best_passive_pr
            self.rms_error = best_passive_err
            self.fit_kwargs = {"passive": True, **best_passive_kwargs}
        elif best_non_passive_err is not None:
            pole_residue = best_non_passive_pr
            self.rms_error = best_non_passive_err
            self.fit_kwargs = {"passive": False, **best_non_passive_kwargs}
        else:
            with self._lock:
                self._status = {"message": "error", "progress": 100}
            raise RuntimeError(
                f"Unable to obtain a fit for '{component_name}' within {rms_error_tolerance} RMS "
                f"error tolerance."
            )

        if self.rms_error > rms_error_tolerance:
            warnings.warn(
                f"Fitting error '{self.rms_error:.6g}' larger than 'rms_error_tolerance' "
                f"{rms_error_tolerance:.6g} for '{component_name}'.",
                RuntimeWarning,
                2,
            )
        if passive and not self.fit_kwargs["passive"]:
            warnings.warn(f"Fitting is not passive for '{component_name}'.", RuntimeWarning, 2)

        self.time_domain_model = TimeDomainModel(pole_residue, time_step)
        _pole_residue_fit_cache[self._cache_key] = (
            self.s_matrix.copy(),
            dict(fit_kwargs),
            self.rms_error,
            pole_residue.copy(),
        )
        with self._lock:
            self._status = {"message": "success", "progress": 100}
        return


register_time_stepper_class(SMatrixTimeStepper)
config.default_time_steppers["*"] = SMatrixTimeStepper()
