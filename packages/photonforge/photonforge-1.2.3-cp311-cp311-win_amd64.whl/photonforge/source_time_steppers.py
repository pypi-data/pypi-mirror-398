import warnings
from collections.abc import Sequence
from math import gamma
from typing import Literal

import numpy
from numpy.random import SeedSequence, default_rng
from scipy.integrate import solve_ivp

from .extension import Component, TimeStepper, _prbs7, _prbs15, _prbs31, register_time_stepper_class
from .modulator_time_steppers import _impedance_warning
from .typing import (
    Angle,
    Fraction,
    Frequency,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    Power,
    Time,
    TimeDelay,
    annotate,
)
from .utils import C_0, H, Q

RIN = annotate(NonNegativeFloat, label="Relative Intensity Noise", units="1/Hz")


class CWLaserTimeStepper(TimeStepper):
    r"""Time-stepper for a continuous-wave (CW) laser source.

    This model generates a complex optical field with a constant average
    power. It can optionally include phase noise, modeled as a Lorentzian
    line width, and relative intensity noise (RIN) from a white noise
    process. The output field has the form:

    .. math:: A[k] = \sqrt{P[k]} e^{j\phi[k]}

    The phase noise is modeled as a discrete-time Wiener process. The phase
    increment at each step is a Gaussian random variable with variance
    determined by the linewidth Δν as:

    .. math:: \text{Var}[\Delta\phi] = 2\pi \Delta\nu \Delta t

    RIN is modeled as an additive white noise process on the optical power.
    The variance of the power fluctuations is derived from the RIN PSD,
    band-limited by the simulation's Nyquist frequency, and clamped at zero:

    .. math:: \text{Var}[P] \approx \text{RIN} \frac{P_0^2}{2\Delta t}

    Args:
        power: Mean optical output power.
        rel_intensity_noise: One-sided relative intensity noise (RIN) power
          spectral density.
        linewidth: Full-width at half-maximum (FWHM) of the laser's
          Lorentzian shape.
        frequency: Absolute laser frequency. If ``None``, equals the carrier
          frequency. If detuned from the carrier by Δf, the output envelope
          rotates at 2πΔf.
        phase: Starting phase of the output envelope.
        reflection: Reflection coefficient for incident fields.
        seed: Random number generator seed to ensure reproducibility.
    """

    def __init__(
        self,
        *,
        power: Power = 1,
        rel_intensity_noise: RIN = 0,
        linewidth: Frequency = 0,
        frequency: Frequency | None = None,
        phase: Angle = 0,
        reflection: complex = 0,
        seed: NonNegativeInt | None = None,
    ):
        super().__init__(
            power=power,
            rel_intensity_noise=rel_intensity_noise,
            linewidth=linewidth,
            frequency=frequency,
            phase=phase,
            reflection=reflection,
            seed=seed,
        )

    def setup_state(
        self, *, component: Component, time_step: TimeDelay, carrier_frequency: Frequency, **kwargs
    ):
        """Initialize internal state.

        Args:
            component: Component representing the laser source.
            time_step: The interval between time steps (in seconds).
            carrier_frequency: The carrier frequency used to construct the time
              stepper. The carrier should be omitted from the input signals, as
              it is handled automatically by the time stepper.
            kwargs: Unused.
        """
        ports = component.select_ports("optical")
        if len(ports) != 1:
            raise RuntimeError(
                "CWLaserTimeStepper can only be used in components with 1 optical port."
            )
        self._port = next(iter(ports)) + "@0"

        p = self.parametric_kwargs

        self._r = complex(p["reflection"])

        self._power = abs(p["power"])
        self._power_stdev = (
            0
            if p["rel_intensity_noise"] <= 0
            else (self._power * (0.5 * p["rel_intensity_noise"] / time_step) ** 0.5)
        )

        frequency = p["frequency"]
        detuning = 0 if (frequency is None) else (frequency - carrier_frequency)
        self._phase_step = -2.0 * numpy.pi * detuning * time_step
        self._phase_stdev = (
            0 if p["linewidth"] <= 0 else (2.0 * numpy.pi * p["linewidth"] * time_step) ** 0.5
        )

        self._seed = SeedSequence() if p["seed"] is None else p["seed"]
        self.reset()

    def reset(self):
        """Reset internal state."""
        self._phase = self.parametric_kwargs["phase"] / 180 * numpy.pi
        self._rng = default_rng(self._seed)
        self._sample()

    def _sample(self):
        power = self._power
        if self._power_stdev > 0:
            power += self._rng.normal(0, self._power_stdev)
        self._output = max(0, power) ** 0.5 * numpy.exp(1j * self._phase)
        self._phase += self._phase_step
        if self._phase_stdev > 0:
            self._phase += self._rng.normal(0, self._phase_stdev)

    def step_single(
        self,
        inputs: dict[str, complex],
        time_index: int,
        update_state: bool,
        shutdown: bool,
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
        output = {self._port: self._output + self._r * inputs.get(self._port, 0)}
        if update_state:
            self._sample()
        return output


def _rate_equations(t, y, current, stepper):
    p, n, _ = y

    delta_n = n - stepper._n0
    g = stepper._vg_a0 / (1.0 + stepper._eps * p)
    g_uncompressed = stepper._gamma * stepper._vg_a0 * delta_n

    dp_dt = (stepper._gamma * g * delta_n - 1 / stepper._tau_p) * p + (
        stepper._beta * stepper._gamma * n
    ) / stepper._tau_n
    dn_dt = current / (stepper._q_va) - g * delta_n * p - n / stepper._tau_n
    dphi_dt = 0.5 * stepper._alpha * (g_uncompressed - 1.0 / stepper._tau_p)

    return [dp_dt, dn_dt, dphi_dt]


class DMLaserTimeStepper(TimeStepper):
    r"""Time-stepper for a directly modulated laser source.

    This model solves the single-mode semiconductor laser rate equations for
    photon density (:math:`p`), carrier density (:math:`n`), and optical
    phase (:math:`\phi`). The model includes gain compression, and intensity
    and phase noises (implemented similarly to :class:`CWLaserTimeStepper`).

    The rate equations are:

    .. math::

       \frac{{\rm d} p}{{\rm d} t} &= \Gamma G(p) (n-n_0) p
            - \frac{p}{\tau_p} + \frac{\beta\Gamma}{\tau_n}n

       \frac{{\rm d} n}{{\rm d} t} &= \frac{I(t)}{q V_a} - G(p) (n-n_0) p
            - \frac{n}{\tau_n}

       \frac{{\rm d} \phi}{{\rm d} t} &= \frac{\alpha}{2}
            \left(\Gamma v_g a_0 (n-n_0) - \frac{1}{\tau_p}\right)

       G(p) &= \frac{c_0}{n_g} \frac{a_0}{1 + \epsilon p}

    From the solution of the rate equations at each time step, the
    instantaneous output power and complex field amplitude  for a carrier
    with frequency :math:`f_c` are:

    .. math::

       P_\text{out} &= \frac{\eta_0 h f_c V_a}{2 \Gamma \tau_p} p

       A &= \sqrt{P_\text{out}} e^{j\phi}

    Args:
        quantum_efficiency: Total quantum efficiency (:math:`\eta_0`) for
          power calibration.
        spontaneous_emission_factor: Fraction of spontaneous emission
          coupled into the lasing mode (:math`\beta`).
        carrier_lifetime: Effective carrier recombination lifetime
          (:math:`\tau_n`).
        gain_compression_factor: Gain compression coefficient
          (:math:`\epsilon`).
        transparency_carrier_density: Transparency carrier density
          (:math:`n_0`).
        differential_gain: Differential material gain coefficient
          (:math:`a_0`).
        n_group: Optical group index in the gain medium (:math:`n_g`).
        linewidth_enhancement_factor: Henry's α factor (:math:`\alpha`) for
          AM-FM coupling.
        confinement_factor: Modal confinement in the active region
          (:math:`\Gamma`).
        photon_lifetime: Photon lifetime in the optical cavity
          (:math:`\tau_p`).
        active_region_volume: Volume of the active gain region
          (:math:`V_a`).
        rel_intensity_noise: One-sided relative intensity noise (RIN) power
          spectral density.
        linewidth: Full-width at half-maximum (FWHM) of the laser's
          Lorentzian shape.
        reflection: Reflection coefficient for incident fields.
        seed: Random number generator seed to ensure reproducibility.

    References:
        1. Coldren, L. A., Corzine, S. W., & Ma, M. L. (2012). *Diode Lasers
           and Photonic Integrated Circuits*. Wiley.

        2. Agrawal, G. P., & Dutta, N. K. (1993). *Semiconductor Lasers*.
           Van Nostrand Reinhold.
    """

    def __init__(
        self,
        *,
        quantum_efficiency: NonNegativeFloat,
        spontaneous_emission_factor: NonNegativeFloat,
        carrier_lifetime: annotate(PositiveFloat, units="s"),
        gain_compression_factor: annotate(NonNegativeFloat, units="m³"),
        transparency_carrier_density: annotate(NonNegativeFloat, units="m⁻³"),
        differential_gain: annotate(NonNegativeFloat, units="m³/s"),
        n_group: NonNegativeFloat,
        linewidth_enhancement_factor: NonNegativeFloat,
        confinement_factor: PositiveFloat,
        photon_lifetime: annotate(PositiveFloat, units="s"),
        active_region_volume: annotate(PositiveFloat, units="m³"),
        rel_intensity_noise: RIN = 0,
        linewidth: Frequency = 0,
        reflection: complex = 0,
        seed: NonNegativeInt | None = None,
    ):
        super().__init__(
            quantum_efficiency=quantum_efficiency,
            spontaneous_emission_factor=spontaneous_emission_factor,
            carrier_lifetime=carrier_lifetime,
            gain_compression_factor=gain_compression_factor,
            transparency_carrier_density=transparency_carrier_density,
            differential_gain=differential_gain,
            n_group=n_group,
            linewidth_enhancement_factor=linewidth_enhancement_factor,
            confinement_factor=confinement_factor,
            photon_lifetime=photon_lifetime,
            active_region_volume=active_region_volume,
            rel_intensity_noise=rel_intensity_noise,
            linewidth=linewidth,
            reflection=reflection,
            seed=seed,
        )

    def setup_state(
        self, *, component: Component, time_step: TimeDelay, carrier_frequency: Frequency, **kwargs
    ):
        """Initialize internal state.

        Args:
            component: Component representing the laser source.
            time_step: The interval between time steps (in seconds).
            carrier_frequency: The carrier frequency used to determine the
              photon energy in the model.
            kwargs: Unused.
        """
        global _impedance_warning

        if _impedance_warning:
            _impedance_warning = False
            warnings.warn(
                "Time-domain models convert between field amplitudes to voltages and currents "
                "using a fixed 50Ω reference. This behavior will change in the future and the "
                "actual port impedance will be used.",
                FutureWarning,
                stacklevel=2,
            )

        if carrier_frequency <= 0:
            raise ValueError(
                "DMLaserTimeStepper setup requires a positive 'carrier_frequency' to derive the "
                "photon energy of the generated emission."
            )

        ports = component.select_ports("optical")
        e_ports = component.select_ports("electrical")
        if len(ports) != 1 or len(e_ports) != 1:
            raise RuntimeError(
                "PhotodiodeTimeStepper can only be used in components with 1 optical port and 1 "
                "electrical port."
            )
        self._port = next(iter(ports)) + "@0"
        self._e_port = next(iter(e_ports)) + "@0"

        self._time_step = time_step

        p = self.parametric_kwargs
        self._r = complex(p["reflection"])
        self._kp = float(
            (H * carrier_frequency * p["quantum_efficiency"] * p["active_region_volume"])
            / (2.0 * p["confinement_factor"] * p["photon_lifetime"])
        )
        self._vg_a0 = C_0 * 1e-6 / p["n_group"] * p["differential_gain"]
        self._tau_n = p["carrier_lifetime"]
        self._gamma = p["confinement_factor"]
        self._eps = p["gain_compression_factor"]
        self._alpha = p["linewidth_enhancement_factor"]
        self._tau_p = p["photon_lifetime"]
        self._beta = p["spontaneous_emission_factor"]
        self._n0 = p["transparency_carrier_density"]
        self._q_va = Q * p["active_region_volume"]

        self._rel_power_stdev = (
            0
            if p["rel_intensity_noise"] <= 0
            else (0.5 * p["rel_intensity_noise"] / time_step) ** 0.5
        )
        self._phase_stdev = (
            0 if p["linewidth"] <= 0 else (2.0 * numpy.pi * p["linewidth"] * time_step) ** 0.5
        )

        self._seed = SeedSequence() if p["seed"] is None else p["seed"]
        self.reset()

    def reset(self):
        """Reset internal state."""
        self._rng = default_rng(self._seed)
        self._p = 1e-9
        self._n = self._n0
        self._phi = self._rng.uniform(0, 2 * numpy.pi)
        self._sample_noise()

    def _sample_noise(self):
        self._rel_noise = (
            self._rng.normal(0, self._rel_power_stdev) if self._rel_power_stdev > 0 else 0
        )
        self._phase_noise = self._rng.normal(0, self._phase_stdev) if self._phase_stdev > 0 else 0

    def step_single(
        self,
        inputs: dict[str, complex],
        time_index: int,
        update_state: bool,
        shutdown: bool,
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
        current = inputs.get(self._e_port, 0).real / 50**0.5

        # Solve rate equations
        sol = solve_ivp(
            _rate_equations,
            t_span=(0, self._time_step),
            y0=[self._p, self._n, self._phi],
            method="BDF",
            t_eval=[self._time_step],
            args=(current, self),
        )
        if not sol.success:
            raise RuntimeError(f"Error solving rate equations: {sol.message}")

        p, n, phi = sol.y[:, -1]
        p = max(0, self._kp * p * (1 + self._rel_noise))

        # Instantaneous (noisy) power and stored phase
        output = {
            self._port: p**0.5 * numpy.exp(-1j * self._phi) + self._r * inputs.get(self._port, 0)
        }

        if update_state:
            self._sample_noise()
            self._p = p / self._kp if self._kp > 0 else 0.0
            self._n = max(0.0, n)
            self._phi = phi + self._phase_noise

        return output


class OpticalPulseTimeStepper(TimeStepper):
    r"""Time-stepper for a Gaussian optical pulse source.

    Args:
        energy: Total pulse energy.
        width: Full-width at half-maximum (FWHM) of the pulse intensity.
        offset: Time shift for the center of the first pulse. If ``None``,
          a value is chosen automatically.
        repetition_rate: If positive, generates a periodic train of pulses
          at this rate.
        phase: Phase shift applied to the pulse. A sequence of values can be
          used to define the phase of each pulse in a periodic train. The
          sequence is wrapped around if necessary.
        chirp: Chirp parameter for adding quadratic phase across the pulse.
        order: Order of the super-Gaussian pulse.
        frequency: Absolute laser frequency. If ``None``, equals the carrier
          frequency. If detuned from the carrier by Δf, the output envelope
          rotates at 2πΔf.
        rel_intensity_noise: One-sided relative intensity noise (RIN) power
          spectral density.
        linewidth: Full-width at half-maximum (FWHM) of the laser's
          Lorentzian shape.
        jitter: RMS clock jitter for pulse trains.
        prbs: PRBS polinomial degree. Value 0 disables PRBS.
        reflection: Reflection coefficient for incident fields.
        seed: Random number generator seed to ensure reproducibility.

    Note:
        The phase added by the chirp factor :math:`C` to each pulse centered
        at :math:`t_0` is :math:`\frac{C (t-t_0)^2}{2 \sigma^2}`, in which
        :math:`\sigma` is the half-width at :math:`e^{-1}` amplitude.

    Important:
        The effective clock jitter can be larger than specified due to the
        size of the time step. The larger the ``jitter`` value w.r.t the
        ``time_step``, the better it can be simulated.
    """

    def __init__(
        self,
        *,
        energy: annotate(NonNegativeFloat, units="J"),
        width: TimeDelay,
        offset: TimeDelay | None = None,
        repetition_rate: Frequency = 0,
        phase: Angle | Sequence[Angle] = 0,
        chirp: Angle = 0,
        order: annotate(float, minimum=1) = 1,
        frequency: Frequency | None = None,
        rel_intensity_noise: RIN = 0,
        linewidth: Frequency = 0,
        jitter: TimeDelay = 0,
        prbs: Literal[0, 7, 15, 31] = 0,
        reflection: complex = 0,
        seed: NonNegativeInt | None = None,
    ):
        super().__init__(
            energy=energy,
            width=width,
            offset=offset,
            frequency=frequency,
            repetition_rate=repetition_rate,
            phase=phase,
            chirp=chirp,
            order=order,
            rel_intensity_noise=rel_intensity_noise,
            linewidth=linewidth,
            jitter=jitter,
            prbs=prbs,
            reflection=reflection,
            seed=seed,
        )

    def setup_state(
        self, *, component: Component, time_step: TimeDelay, carrier_frequency: Frequency, **kwargs
    ):
        """Initialize internal state.

        Args:
            component: Component representing the laser source.
            time_step: The interval between time steps (in seconds).
            carrier_frequency: The carrier frequency used to construct the time
              stepper. The carrier should be omitted from the input signals, as
              it is handled automatically by the time stepper.
            kwargs: Unused.
        """
        p = self.parametric_kwargs

        ports = component.select_ports("optical")
        if len(ports) != 1:
            raise RuntimeError(
                "OpticalPulseTimeStepper can only be used in components with 1 optical port."
            )
        self._port = next(iter(ports)) + "@0"

        repetition_rate = p["repetition_rate"]
        if repetition_rate > 0.5 / time_step:
            warnings.warn(
                f"Repetition rate {repetition_rate} Hz exceeds the Nyquist frequency "
                f"{0.5 / time_step} Hz.",
                stacklevel=2,
            )

        self._time_step = time_step
        if repetition_rate > 0:
            self._period = 1 / repetition_rate
            self._prbs = {0: (lambda _: 1), 7: _prbs7, 15: _prbs15, 31: _prbs31}.get(p["prbs"])
            if self._prbs is None:
                raise ValueError(
                    f"Argument 'prbs' must be 7, 15, 31, or None. Value {p['prbs']!r} is invalid."
                )
        else:
            self._period = numpy.inf
            self._prbs = lambda _: 1
            if p["jitter"] != 0:
                warnings.warn("'jitter' has no effect when 'repetition_rate' is 0.", stacklevel=2)
            if p["prbs"] != 0:
                warnings.warn("'prbs' has no effect when 'repetition_rate' is 0.", stacklevel=2)

        width = max(0, p["width"])
        if width <= 5 * time_step:
            warnings.warn(
                f"Gaussian FWHM ({width} s) is narrower than 5 times the time step "
                f"({5 * time_step} s). Consider reducing the time step.",
                stacklevel=2,
            )

        self._order = max(1, p["order"])
        w = 0.5 / self._order
        self._scale = 2 * numpy.log(2) ** w / width
        self._pulse_width = 2 * numpy.log(1e4) ** w / self._scale
        self._amp = (p["energy"] * self._order * self._scale * 2**w / gamma(w)) ** 0.5

        self._phases = p["phase"]
        if numpy.isscalar(self._phases):
            self._phases = [self._phases]

        self._phases = numpy.array(self._phases) / 180 * numpy.pi
        self._chirp = p["chirp"] / 180 * numpy.pi

        frequency = p["frequency"]
        self._w_detuning = (
            0 if (frequency is None) else (2 * numpy.pi * (frequency - carrier_frequency))
        )

        self._rel_amp_stdev = (
            0
            if p["rel_intensity_noise"] <= 0
            else (0.5 * p["rel_intensity_noise"] / time_step) ** 0.5
        )
        self._phase_stdev = (
            0 if p["linewidth"] <= 0 else (2.0 * numpy.pi * p["linewidth"] * time_step) ** 0.5
        )
        self._period_stdev = p["jitter"]
        self._seed = SeedSequence() if p["seed"] is None else p["seed"]
        self.reset()

    def reset(self):
        """Reset internal state."""
        p = self.parametric_kwargs
        self._output = None
        self._start = None if p["offset"] is None else (p["offset"] - self._pulse_width / 2)
        self._period_end = None
        self._phase_counter = -1
        num_pulses = (
            int(numpy.ceil(self._pulse_width / self._period)) if numpy.isfinite(self._period) else 1
        )
        self._pulses = [[None, None] for _ in range(num_pulses)]
        self._pulse_index = 0
        self._rng = default_rng(self._seed)
        self._prbs_state = int(self._rng.integers(1, 2 ** (p["prbs"] or 1)))

    def _sample_jitter(self):
        return self._rng.normal(0, self._period_stdev) if self._period_stdev > 0 else 0

    def _sample_rel_noise(self):
        return 1 + (self._rng.normal(0, self._rel_amp_stdev) if self._rel_amp_stdev > 0 else 0)

    def _sample_prbs(self):
        self._prbs_state = self._prbs(self._prbs_state)
        return self._prbs_state & 1

    def _next_phase(self):
        self._phase_counter = (self._phase_counter + 1) % self._phases.size
        return self._phases[self._phase_counter]

    def _sample_phase_noise(self):
        return self._rng.normal(0, self._phase_stdev) if self._phase_stdev > 0 else 0

    def _sample(self, t, t0, phase):
        x = (self._scale * (t - t0)) ** 2
        phase += self._w_detuning * t + self._chirp * x
        return self._amp * numpy.exp(-(x**self._order) + 1j * phase)

    def step_single(
        self,
        inputs: dict[str, complex],
        time_index: int,
        update_state: bool,
        shutdown: bool,
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
        if self._output is None:
            time = time_index * self._time_step
            self._output = 0
            if self._start is None:
                self._start = time
            if self._start <= time:
                while self._start + self._period <= time:
                    self._start += self._period
                self._period_end = self._start + self._period + self._sample_jitter()
                if self._sample_prbs():
                    t0 = self._start + self._pulse_width / 2
                    phase = self._next_phase() + self._sample_phase_noise()
                    self._pulses[0] = t0, phase
                    self._output = self._sample(time, t0, phase) * self._sample_rel_noise()

        output = {self._port: self._output}

        if update_state:
            time = (time_index + 1) * self._time_step
            if self._period_end is None:
                if self._start <= time:
                    self._period_end = self._start + self._period + self._sample_jitter()
                    if self._sample_prbs():
                        t0 = self._start + self._pulse_width / 2
                        self._pulses[0] = t0, self._next_phase()
            elif time >= self._period_end:
                if self._sample_prbs():
                    t0 = self._period_end + self._pulse_width / 2
                    self._pulse_index = (self._pulse_index + 1) % len(self._pulses)
                    self._pulses[self._pulse_index] = t0, self._next_phase()
                self._period_end += self._period + self._sample_jitter()

            pulse = 0
            for i, (t0, phase) in enumerate(self._pulses):
                if t0 is None:
                    continue
                phase += self._sample_phase_noise()
                self._pulses[i] = t0, phase
                pulse += self._sample(time, t0, phase)
            self._output = pulse * self._sample_rel_noise()

        return output


class OpticalNoiseTimeStepper(TimeStepper):
    r"""Time-stepper for an optical white-noise source.

    This model generates zero-mean, circularly symmetric complex Gaussian
    noise. It is a memoryless source, producing a new independent sample at
    each time step.

    Args:
        noise: One-sided, amplitude spectral density (ASD) of noise.
        reflection: Reflection coefficient for incident fields.
        seed: Random number generator seed to ensure reproducibility.
    """

    def __init__(
        self,
        *,
        noise: annotate(NonNegativeFloat, units="√(W/Hz)"),
        reflection: complex = 0,
        seed: NonNegativeInt | None = None,
    ):
        super().__init__(noise=noise, reflection=reflection, seed=seed)

    def setup_state(self, *, component: Component, time_step: TimeDelay, **kwargs):
        """Initialize internal state.

        Args:
            component: Component representing the noise source.
            time_step: The interval between time steps (in seconds).
            kwargs: Unused.
        """
        ports = component.select_ports("optical")
        if len(ports) != 1:
            raise RuntimeError(
                "OpticalNoiseTimeStepper can only be used in components with 1 optical port."
            )
        self._port = next(iter(ports)) + "@0"

        p = self.parametric_kwargs

        self._r = complex(p["reflection"])
        self._stdev = 0.5 * abs(p["noise"]) / time_step**0.5
        self._seed = SeedSequence() if p["seed"] is None else p["seed"]
        self.reset()

    def reset(self):
        """Reset internal state."""
        self._rng = default_rng(self._seed)
        self._sample()

    def _sample(self):
        self._output = self._rng.normal(0, self._stdev) + 1j * self._rng.normal(0, self._stdev)

    def step_single(
        self,
        inputs: dict[str, complex],
        time_index: int,
        update_state: bool,
        shutdown: bool,
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
        output = {self._port: self._output + self._r * inputs.get(self._port, 0)}
        if update_state:
            self._sample()
        return output


class WaveformTimeStepper(TimeStepper):
    """Time-stepper for a signal generator from several waveforms.

    Args:
        frequency: Source frequency. The carrier frequency, if any, is *not*
          taken into account. The generated signals are always real. This is
          equivalent to the bit rate for PRBS signals.
        amplitude: Source amplitude. Sine and triangle waves range from
          ``offset - amplitude`` to ``offset + amplitude``. Other waveforms
          range from ``offset`` to ``offset + amplitude``.
        offset: Constant source offset.
        start: Start time of the source.
        stop: Stop time of the source. The effective stop time is after the
          current pulse finishes, so it can be after ``stop``.
        waveform: Source waveform.
        skew: Triangle wave asymmetry parameter. A value of 1 produces a
          sawtooth wave, whereas a value of 0, a reversed sawtooth.
        width: Full-width at half-maximum (FWHM) for trapezoid, raised-
          cosine, and Gaussian pulses, as a fraction of the source period.
        rise: Trapezoidal and raised-cosine pulses rise time, as a fraction
          of the source period.
        fall: Trapezoidal and raised-cosine pulses fall time, as a fraction
          of the source period.
        order: Order of the super-Gaussian pulse.
        noise: One-sided, amplitude spectral density (ASD) of noise.
        jitter: RMS clock jitter.
        prbs: PRBS polinomial degree. Value 0 disables PRBS.
        seed: Random number generator seed to ensure reproducibility.

    Note:
        Pseudorandom bit sequences (PRBS) can be used with any waveform, but
        trapezoid and raised-cosine are more appropriate. With those,
        return-to-zero (RZ) coding can be set with ``width = 0.5``, and
        non-return-to-zero (NRZ) with ``width = 1 + 0.5 * (rise + fall)``.

    Important:
        The effective clock jitter can be larger than specified due to the
        size of the time step. The larger the ``jitter`` value w.r.t the
        ``time_step``, the better it can be simulated.
    """

    def __init__(
        self,
        *,
        frequency: Frequency,
        amplitude: annotate(float, units="√W") = 1,
        offset: annotate(float, units="√W") = 0,
        start: Time | None = None,
        stop: Time | None = None,
        waveform: Literal["sine", "triangle", "trapezoid", "raised-cosine", "gaussian"] = "sine",
        skew: Fraction = 0.5,
        width: NonNegativeFloat = 0.5,
        rise: NonNegativeFloat = 0,
        fall: NonNegativeFloat = 0,
        order: annotate(float, minimum=1) = 1,
        noise: annotate(NonNegativeFloat, units="√(W/Hz)") = 0,
        jitter: TimeDelay = 0,
        prbs: Literal[0, 7, 15, 31] = 0,
        seed: NonNegativeInt | None = None,
    ):
        super().__init__(
            frequency=frequency,
            amplitude=amplitude,
            offset=offset,
            start=start,
            stop=stop,
            skew=skew,
            width=width,
            rise=rise,
            fall=fall,
            order=order,
            noise=noise,
            jitter=jitter,
            seed=seed,
            waveform=waveform,
            prbs=prbs,
        )

    def setup_state(self, *, component: Component, time_step: TimeDelay, **kwargs):
        """Initialize internal state.

        Args:
            component: Component representing the laser source.
            time_step: The interval between time steps (in seconds).
            kwargs: Unused.
        """
        p = self.parametric_kwargs

        ports = component.select_ports("electrical")
        if len(ports) != 1:
            raise RuntimeError(
                "WaveformTimeStepper can only be used in components with 1 electrical port."
            )
        self._port = next(iter(ports)) + "@0"

        freq = p["frequency"]
        if freq > 0.5 / time_step:
            warnings.warn(
                f"Base frequency {freq} Hz exceeds the Nyquist frequency {0.5 / time_step} Hz.",
                stacklevel=2,
            )

        self._time_step = time_step
        self._original_period = 1 / freq if freq > 0 else numpy.inf
        self._amp = abs(float(p["amplitude"]))
        self._offset = p["offset"]

        self._stop = p["stop"]
        if self._stop is None:
            self._stop = numpy.inf

        self._prbs = {0: (lambda _: 1), 7: _prbs7, 15: _prbs15, 31: _prbs31}.get(p["prbs"])
        if self._prbs is None:
            raise ValueError(
                f"Argument 'prbs' must be 7, 15, 31, or None. Value {p['prbs']!r} is invalid."
            )

        waveform = p["waveform"]
        if waveform == "sine":
            self._sample = self._sine_sample
            self._pulse_width = 1
        elif waveform == "triangle":
            self._sample = self._triangle_sample
            self._skew = min(1, max(0, p["skew"]))
            self._pulse_width = 1
        elif waveform == "trapezoid":
            self._sample = self._trapezoid_sample
            self._rise = max(0, p["rise"])
            self._fall = max(0, p["fall"])
            self._ceil = (self._rise - self._fall) / 2 + max(0, p["width"])
            self._pulse_width = self._ceil + self._fall
        elif waveform == "raised-cosine":
            self._sample = self._raised_cosine_sample
            self._rise = max(0, p["rise"])
            self._fall = max(0, p["fall"])
            self._ceil = (self._rise - self._fall) / 2 + max(0, p["width"])
            self._pulse_width = self._ceil + self._fall
        elif waveform == "gaussian":
            self._sample = self._gaussian_sample
            width = p["width"]
            self._order = max(1, p["order"])
            w = 0.5 / self._order
            self._scale = 2 * numpy.log(2) ** w / width
            self._pulse_width = 2 * numpy.log(1e3) ** w / self._scale

            if width * self._original_period <= 5 * time_step:
                warnings.warn(
                    f"Gaussian FWHM ({width} × {self._original_period} s) is narrower than 5 times "
                    f"the time step ({5 * time_step} s). Consider reducing the time step.",
                    stacklevel=2,
                )
        else:
            raise RuntimeError(f"Unknown waveform {waveform!r}.")

        self._amp_stdev = 0 if p["noise"] <= 0 else (p["noise"] * (0.5 / time_step) ** 0.5)
        self._period_stdev = p["jitter"]
        self._seed = SeedSequence() if p["seed"] is None else p["seed"]
        self.reset()

    def reset(self):
        """Reset internal state."""
        p = self.parametric_kwargs
        self._output = None
        self._start = p["start"]
        self._period_end = None
        self._pulses = [(None, None)] * min(4, max(1, int(numpy.ceil(self._pulse_width))))
        self._pulse_index = 0
        self._rng = default_rng(self._seed)
        self._prbs_state = int(self._rng.integers(1, 2 ** (p["prbs"] or 1)))

    def _update_jitter(self):
        self._period = (
            self._rng.normal(self._original_period, self._period_stdev)
            if self._period_stdev > 0
            else self._original_period
        )

    def _sample_noise(self):
        return self._rng.normal(0, self._amp_stdev) if self._amp_stdev > 0 else 0

    def _sample_prbs(self):
        self._prbs_state = self._prbs(self._prbs_state)
        return self._prbs_state & 1

    def _sine_sample(self, tau):
        return numpy.sin(2 * numpy.pi * tau)

    def _triangle_sample(self, tau):
        tau = (tau + self._skew / 2) % 1
        if self._skew == 0:
            y = 1 - 2 * tau
        elif self._skew == 1:
            y = -1 + 2 * tau
        elif tau < self._skew:
            y = -1 + 2 * tau / self._skew
        else:
            y = 1 - 2 * (tau - self._skew) / (1 - self._skew)
        return y

    def _trapezoid_sample(self, tau):
        if tau < self._rise:
            y = (tau / self._rise) if self._rise > 0 else 1
        elif tau < self._ceil:
            y = 1
        elif tau < self._pulse_width:
            y = (1 - (tau - self._ceil) / self._fall) if self._fall > 0 else 0
        else:
            y = 0
        return y

    def _raised_cosine_sample(self, tau):
        if tau < self._rise:
            y = (0.5 - 0.5 * numpy.cos(numpy.pi * tau / self._rise)) if self._rise > 0 else 1
        elif tau < self._ceil:
            y = 1
        elif tau < self._pulse_width:
            y = (
                (0.5 + 0.5 * numpy.cos(numpy.pi * (tau - self._ceil) / self._fall))
                if self._fall > 0
                else 0
            )
        else:
            y = 0
        return y

    def _gaussian_sample(self, tau):
        return numpy.exp(-(abs(self._scale * (tau - self._pulse_width / 2)) ** (2 * self._order)))

    def step_single(
        self,
        inputs: dict[str, complex],
        time_index: int,
        update_state: bool,
        shutdown: bool,
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
        if self._output is None:
            time = time_index * self._time_step

            if self._start is None:
                self._start = time
            if self._start <= time:
                while self._start + self._original_period <= time:
                    self._start += self._original_period
                self._update_jitter()
                self._period_end = self._start + self._period

            self._output = self._offset + self._sample_noise()
            if self._start <= time < self._stop and self._sample_prbs():
                self._pulses[0] = self._start, 0
                self._output += self._amp * self._sample(0)

        output = {self._port: self._output}

        if update_state:
            time = (time_index + 1) * self._time_step

            if self._period_end is None:
                if self._start <= time:
                    self._update_jitter()
                    self._period_end = self._start + self._period
                    if time < self._stop and self._sample_prbs():
                        self._pulses[0] = self._start, 0
            elif time >= self._period_end:
                for i, (start, tau0) in enumerate(self._pulses):
                    if start is not None:
                        tau = tau0 + (time - start) / self._period
                        self._pulses[i] = time, tau
                if time < self._stop and self._sample_prbs():
                    self._pulse_index = (self._pulse_index + 1) % len(self._pulses)
                    self._pulses[self._pulse_index] = self._period_end, 0
                self._update_jitter()
                self._period_end += self._period

            pulse = 0
            for i, (start, tau0) in enumerate(self._pulses):
                if start is not None:
                    tau = tau0 + (time - start) / self._period
                    if tau > self._pulse_width:
                        self._pulses[i] = None, None
                    else:
                        pulse += self._sample(tau)
            self._output = self._offset + self._sample_noise() + self._amp * min(1, max(-1, pulse))

        return output


register_time_stepper_class(CWLaserTimeStepper)
register_time_stepper_class(DMLaserTimeStepper)
register_time_stepper_class(OpticalPulseTimeStepper)
register_time_stepper_class(OpticalNoiseTimeStepper)
register_time_stepper_class(WaveformTimeStepper)
