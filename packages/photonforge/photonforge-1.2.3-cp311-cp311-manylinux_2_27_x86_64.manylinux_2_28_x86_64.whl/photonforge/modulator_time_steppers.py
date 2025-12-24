import warnings

import numpy

from .extension import Component, TimeStepper, register_time_stepper_class
from .typing import Coordinate, Frequency, PropagationLoss, TimeDelay, annotate
from .utils import C_0, route_length

_impedance_warning = True


class PhaseModTimeStepper(TimeStepper):
    r"""Time-stepper for a uniform electro-optic phase modulator.

    This model implements a two-port optical phase modulator with a single
    electrical drive. It features a length-aware phase modulation law with
    optional nonlinear terms, a voltage-dependent loss model, and an
    optional first-order low-pass filter on the electrical input to model
    finite bandwidth. The optical path includes group delay based on a
    constant group index.

    The induced phase shift and optical loss are given by:

    .. math::

       \Delta\phi &= \frac{\pi V \ell}{V_{\pi L}}
         + k_2 V^2 \ell + k_3 V^3 \ell

       L &= \left(L_p + \frac{{\rm d}L_p}{{\rm d}V} V
         + \frac{{\rm d}^2 L_p}{{\rm d}V^2} V^2 \right) \ell

    Notes:
        The total loss is clamped are 0 dB to avoid gain.

        The group delay :math:`n_g \ell / c_0` is implemented as a fixed
        multiple of the time step.

    Args:
        length: Physical length of the modulator segment.
        n_eff: Effective index of the optical mode at the carrier frequency.
        n_group: Group index of the optical mode, used to calculate delay.
        v_piL: Electro-optic phase coefficient :math:`V_{\pi L}`.
        propagation_loss: Optical propagation loss.
        k2: Quadratic nonlinear phase coefficient.
        k3: Cubic nonlinear phase coefficient.
        dloss_dv: Linear voltage-dependent optical loss coefficient.
        dloss_dv2: Quadratic voltage-dependent optical loss coefficient.
        tau_rc: Time constant of the optional first-order low-pass filter
          for the electrical input. Only active for positive values.
    """

    def __init__(
        self,
        *,
        length: Coordinate | None = None,
        n_eff: float,
        n_group: float = 0,
        v_piL: annotate(float, label="VπL", units="V·μm") = 0,
        propagation_loss: PropagationLoss = 0,
        k2: annotate(float, label="k₂", units="rad/μm/V²") = 0,
        k3: annotate(float, label="k₃", units="rad/μm/V³") = 0,
        dloss_dv: annotate(float, label="dL/dV", units="dB/μm/V") = 0,
        dloss_dv2: annotate(float, label="d²L/dV²", units="dB/μm/V²") = 0,
        tau_rc: TimeDelay = 0,
    ):
        super().__init__(
            length=length,
            n_eff=n_eff,
            n_group=n_group,
            v_piL=v_piL,
            propagation_loss=propagation_loss,
            k2=k2,
            k3=k3,
            dloss_dv=dloss_dv,
            dloss_dv2=dloss_dv2,
            tau_rc=tau_rc,
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

        ports = sorted(component.select_ports("optical"))
        e_port = tuple(component.select_ports("electrical"))
        if len(ports) != 2 or len(e_port) != 1:
            raise RuntimeError(
                "PhaseModTimeStepper can only be used in components with 2 optical and 1 "
                "electrical ports."
            )
        self._e = e_port[0] + "@0"
        self._opt0 = ports[0] + "@0"
        self._opt1 = ports[1] + "@0"

        # TODO Time-domain impedance handling? What about dispersion?
        # e_port = component.ports[e_port[0]]
        # self._sqrt_z = e_port.impedance() ** 0.5

        p = self.parametric_kwargs
        length = p["length"]
        if length is None:
            length = 0
            port0 = component.ports[ports[0]]
            port1 = component.ports[ports[1]]
            for _, _, layer in port0.spec.path_profiles_list():
                length = max(length, route_length(component, layer))
            if length <= 0:
                length = numpy.sqrt(numpy.sum((port0.center - port1.center) ** 2))

        self._phi0 = 2.0 * numpy.pi * carrier_frequency * p["n_eff"] * length / C_0
        self._phi1 = (numpy.pi * length / p["v_piL"]) if p["v_piL"] != 0 else 0
        self._phi2 = p["k2"] * length
        self._phi3 = p["k3"] * length

        self._g0 = p["propagation_loss"] * length / -20.0
        self._g1 = p["dloss_dv"] * length / -20.0
        self._g2 = p["dloss_dv2"] * length / -20.0

        self._filter = 0.0 if p["tau_rc"] <= 0 else numpy.exp(-time_step / p["tau_rc"])

        self._delay = max(0, int(numpy.round(p["n_group"] * length / C_0 / time_step)))
        self._buffer = [(0j, 0j) for _ in range(self._delay)]
        self._index = 0

        self._v = 0

    def reset(self):
        """Reset internal state."""
        self._v = 0
        self._buffer = [(0j, 0j) for _ in range(self._delay)]
        self._index = 0

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
        v_in = 50**0.5 * inputs.get(self._e, 0j).real
        v = v_in * (1.0 - self._filter) + self._v * self._filter
        phi = self._phi0 + v * (self._phi1 + v * (self._phi2 + v * self._phi3))
        attenuation = 10.0 ** (self._g0 + v * (self._g1 + v * self._g2))
        factor = attenuation * numpy.exp(1j * phi)

        if self._delay > 0:
            a0, a1 = self._buffer[self._index]
        else:
            a0 = inputs.get(self._opt0, 0j)
            a1 = inputs.get(self._opt1, 0j)

        b0 = factor * a1
        b1 = factor * a0

        if update_state:
            self._v = v
            if self._delay > 0:
                a0 = inputs.get(self._opt0, 0j)
                a1 = inputs.get(self._opt1, 0j)
                self._buffer[self._index] = (a0, a1)
                self._index = (self._index + 1) % self._delay

        return {self._opt0: b0, self._opt1: b1}


register_time_stepper_class(PhaseModTimeStepper)
