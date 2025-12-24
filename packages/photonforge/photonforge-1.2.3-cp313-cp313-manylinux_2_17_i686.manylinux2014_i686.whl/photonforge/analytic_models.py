import copy as libcopy
import io
import json
import struct
import warnings
import zlib
from collections.abc import Sequence
from typing import Any, Literal

import numpy

from . import typing as pft
from .cache import cache_s_matrix
from .extension import (
    Component,
    Interpolator,
    Model,
    Path,
    Port,
    PortSpec,
    Reference,
    SMatrix,
    Technology,
    _from_bytes,
    boolean,
    config,
    frequency_classification,
    register_model_class,
    text,
)
from .tidy3d_model import _ModeSolverRunner
from .utils import C_0, route_length

_ComplexCoeff = pft.array(complex, 0, 2)
_ComplexCoeff1D = pft.array(complex, 0, 1)
_FloatCoeff = pft.array(float, 0, 2)

_bb_layer = (0, 32767)


def _add_bb_text(component, width):
    temp = Component(technology=component.technology)
    temp.add(_bb_layer, *text("BB", width, typeface=1))
    ref = Reference(temp)

    ref_size = ref.size()
    size = component.size()
    if ref_size[0] > 0.8 * size[0] or ref_size[1] > 0.8 * size[1]:
        ref.scale(0.8 * min(size[0] / ref_size[0], size[1] / ref_size[1]))
    elif ref_size[0] < 0.2 * size[0] and ref_size[1] < 0.2 * size[1]:
        ref.scale(0.2 * min(size[0] / ref_size[0], size[1] / ref_size[1]))

    ref.translate(0.5 * (sum(component.bounds()) - sum(ref.bounds())))
    component.add(_bb_layer, *ref.get_structures(_bb_layer))


def _ensure_correct_shape(x: Any, ndims=2) -> numpy.ndarray | Interpolator:
    if isinstance(x, Interpolator):
        if ndims == 1 and isinstance(x.y, list):
            x = Interpolator(x.x, x.y[0], x.method, x.coords)
        elif ndims == 2 and not isinstance(x.y, list):
            x = Interpolator(x.x, [x.y], x.method, x.coords)
        return x
    y = numpy.array(x)
    if y.ndim < ndims:
        shape = (-1,) + (1,) * (ndims - 1)
        y = y.reshape(shape)
    return y


def _sample(
    component_name: str,
    name: str,
    value: numpy.ndarray | Interpolator,
    frequencies: Sequence[float],
    num_modes: int,
) -> numpy.ndarray:
    if isinstance(value, Interpolator):
        value = value(frequencies)
        if value.shape[0] == 1 and num_modes > 1:
            value = numpy.array(numpy.broadcast_to(value, (num_modes, len(frequencies))))
    else:
        shape = (max(num_modes, value.shape[0]), len(frequencies))
        value = numpy.array(numpy.broadcast_to(value, shape))

    if value.shape[0] < num_modes:
        raise RuntimeError(
            f"The first dimension of {name!r} in the model for {component_name!r} must be "
            f"{num_modes} to account for all modes in the component's ports."
        )

    return value[:num_modes]


class ModelResult:
    """DEPRECATED - Model.start may return an SMatrix directly. This class is no longer required."""

    def __init__(self, s_matrix: SMatrix, status: dict[str, Any] | None = None) -> None:
        warnings.warn(
            "ModelResult class is deprecated. The method Model.start may return an SMatrix "
            "instance directly. This class is no longer needed and it will be removed in the "
            "future.",
            FutureWarning,
            stacklevel=2,
        )
        self.status = {"progress": 100, "message": "success"} if status is None else status
        self.s_matrix = s_matrix


class TerminationModel(Model):
    r"""Data model for a 1-port device.

    Args:
        r: Reflection coefficient for the first port. For multimode ports, a
          sequence of coefficients must be provided.

    Notes:
        For multimode ports, mixed-mode coefficients are 0. Dispersion can
        be included in the model by setting the coefficient to an
        :class:`Interpolator` (with multiple values for multimode ports), or
        a 2D array with shape (M, N), in which M is the number of modes, and
        N the length of the frequency sequence used in the S matrix
        computation.
    """

    def __init__(self, r: _ComplexCoeff | Interpolator = 0) -> None:
        super().__init__(r=_ensure_correct_shape(r))

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "termination"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = width * 8

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            component.add(layer, Path((0, 0), w, g).segment((length, 0), 0))

        _add_bb_text(component, width)

        component.add_port(Port((0, 0), 0, port_spec))
        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 1:
            raise RuntimeError(
                f"TerminationModel can only be used on components with 1 port. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        name, port = next(iter(component_ports.items()))

        r = _sample(component.name, "r", self.parametric_kwargs["r"], frequencies, port.num_modes)

        elements = {(f"{name}@{mode}", f"{name}@{mode}"): r[mode] for mode in range(port.num_modes)}
        return SMatrix(frequencies, elements, {name: port})

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "TerminationModel":
        """De-serialize this model."""
        size = struct.calcsize("<BQ")
        version, length = struct.unpack("<BQ", byte_repr[:size])
        if version != 0:
            raise RuntimeError("Unsuported TerminationModel version.")
        if len(byte_repr) != size + length:
            raise ValueError("Unexpected byte representation for TerminationModel")
        mem_io = io.BytesIO()
        mem_io.write(byte_repr[size:])
        mem_io.seek(0)
        coeff = numpy.load(mem_io)
        return cls(coeff)


class TwoPortModel(Model):
    r"""Data model for a 2-port component.

    .. math:: S = \begin{bmatrix}
                     r_0 e^{j \phi}  &   t e^{j \phi}  \\
                      t e^{j \phi}   &  r_1 e^{j \phi} \\
                  \end{bmatrix}

    with dispersion modeled by:

    .. math:: \phi = \frac{2 \pi l_p}{c_0}
         [n_\text{eff} f_0 + n_\text{group} (f - f_0)]

    Args:
        t: Transmission coefficient.
        r0: Reflection coefficient for the first port.
        r1: Reflection coefficient for the second port.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.
        propagation_length: Propagation length :math:`l_p` for dispersion
          modeling.
        n_eff: Effective refractive index for dispersion modeling.
        n_group: Group index. If ``None``, the value of ``n_eff`` is used.
        reference_frequency: Reference frequency :math:`f_0` for dispersion
          calculation. If ``None``, the central frequency is used.

    Notes:
        For multimode ports, a sequence of coefficients must be used, and
        mixed-mode coefficients are 0. Dispersion can be included in the
        model by setting the coefficients to an :class:`Interpolator` (with
        multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        t: _ComplexCoeff | Interpolator = 1,
        r0: _ComplexCoeff | Interpolator = 0,
        r1: _ComplexCoeff | Interpolator = 0,
        ports: pft.annotate(Sequence[str], minItems=2, maxItems=2) | None = None,
        *,
        propagation_length: pft.annotate(float, units="μm") = 0.0,
        n_eff: _ComplexCoeff | Interpolator = 0.0,
        n_group: _FloatCoeff | None = None,
        reference_frequency: pft.Frequency | None = None,
    ) -> None:
        super().__init__(
            t=_ensure_correct_shape(t),
            r0=_ensure_correct_shape(r0),
            r1=_ensure_correct_shape(r1),
            ports=ports,
            propagation_length=propagation_length,
            n_eff=_ensure_correct_shape(n_eff),
            n_group=n_group,
            reference_frequency=reference_frequency,
        )
        if ports is not None and len(ports) != 2:
            raise TypeError(
                f"TwoPortModel can only be used on components with 2 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "wg"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = abs(self.parametric_kwargs["propagation_length"])
        if length == 0.0:
            length = width * 8

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            component.add(layer, Path((0, 0), w, g).segment((length, 0)))

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 2
        component.add_port(Port((0, 0), 0, port_spec), port_names[0])
        component.add_port(Port((length, 0), 180, port_spec), port_names[1])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 2:
            raise RuntimeError(
                f"TwoPortModel can only be used on components with 2 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in TwoPortModel match the {classification} port "
                f"names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"TwoPortModel requires that all component ports have the same number of "
                f"modes. Ports from '{component.name}' support different numbers of modes."
            )

        lp = _ensure_correct_shape(p["propagation_length"])

        f0 = p["reference_frequency"]
        if f0 is None:
            f0 = 0.5 * (frequencies.min() + frequencies.max())

        n_eff = _sample(component.name, "n_eff", p["n_eff"], frequencies, num_modes)
        n_group = p["n_group"]
        if n_group is None:
            n_group = n_eff
        else:
            n_group = _ensure_correct_shape(n_group)

        phase = numpy.exp(
            2j * numpy.pi * lp * ((n_eff - n_group) * f0 + n_group * frequencies) / C_0
        )

        t = _sample(component.name, "t", p["t"], frequencies, num_modes) * phase
        r0 = _sample(component.name, "r0", p["r0"], frequencies, num_modes) * phase
        r1 = _sample(component.name, "r1", p["r1"], frequencies, num_modes) * phase

        s = (
            (r0, t),
            (t, r1),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "TwoPortModel":
        """De-serialize this model."""
        size = struct.calcsize("<B5Q")
        version, *lengths = struct.unpack("<B5Q", byte_repr[:size])
        if version != 0:
            raise RuntimeError("Unsuported TwoPortModel version.")
        coeffs = []
        for length in lengths[:3]:
            mem_io = io.BytesIO()
            mem_io.write(byte_repr[size : size + length])
            mem_io.seek(0)
            coeffs.append(numpy.load(mem_io))
            size += length
        if all(length == 0 for length in lengths[3:]):
            ports = None
        else:
            ports = []
            for length in lengths[3:]:
                ports.append(byte_repr[size : size + length].decode("utf8"))
                size += length
        return cls(*coeffs, ports)


class PowerSplitterModel(Model):
    r"""Data model for a 3-port power splitter.

    .. math:: S = \begin{bmatrix}
                     r_0  &   t   &   t   \\
                      t   &  r_1  &   i   \\
                      t   &   i   &  r_1  \\
                  \end{bmatrix}

    Args:
        t: Transmission coefficient.
        i: Leakage (isolation) coefficient.
        r0: Reflection coefficient for the first port.
        r1: Reflection coefficient for the remaining ports.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.

    Notes:
        For multimode ports, a sequence of coefficients must be used, and
        mixed-mode coefficients are 0. Dispersion can be included in the
        model by setting the coefficients to an :class:`Interpolator` (with
        multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        t: _ComplexCoeff | Interpolator = 2**-0.5,
        i: _ComplexCoeff | Interpolator = 0,
        r0: _ComplexCoeff | Interpolator = 0,
        r1: _ComplexCoeff | Interpolator = 0,
        ports: pft.annotate(Sequence[str], minItems=3, maxItems=3) | None = None,
    ) -> None:
        super().__init__(
            t=_ensure_correct_shape(t),
            i=_ensure_correct_shape(i),
            r0=_ensure_correct_shape(r0),
            r1=_ensure_correct_shape(r1),
            ports=ports,
        )
        if ports is not None and len(ports) != 3:
            raise TypeError(
                f"PowerSplitterModel can only be used on components with 3 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "y-splitter"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = width * 8

        p1 = [(0, 0), (0.25 * length, 0), (0.75 * length, 0.75 * width), (length, 0.75 * width)]
        p2 = [(x, -y) for x, y in p1]

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            polygons = boolean(
                Path(p1[0], w, g).segment(p1[1:]), Path(p2[0], w, g).segment(p2[1:]), "+"
            )
            component.add(layer, *polygons)

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 3
        component.add_port(Port(p1[0], 0, port_spec), port_names[0])
        component.add_port(Port(p2[-1], 180, port_spec), port_names[1])
        component.add_port(Port(p1[-1], 180, port_spec), port_names[2])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 3:
            raise RuntimeError(
                f"PowerSplitterModel can only be used on components with 3 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in PowerSplitterModel match the {classification} "
                f"port names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"PowerSplitterModel requires that all component ports have the same number of "
                f"modes. Ports from '{component.name}' support different numbers of modes."
            )

        t = _sample(component.name, "t", p["t"], frequencies, num_modes)
        i = _sample(component.name, "i", p["i"], frequencies, num_modes)
        r0 = _sample(component.name, "r0", p["r0"], frequencies, num_modes)
        r1 = _sample(component.name, "r1", p["r1"], frequencies, num_modes)

        s = (
            (r0, t, t),
            (t, r1, i),
            (t, i, r1),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "PowerSplitterModel":
        """De-serialize this model."""
        size = struct.calcsize("<B7Q")
        version, *lengths = struct.unpack("<B7Q", byte_repr[:size])
        if version != 0:
            raise RuntimeError("Unsuported PowerSplitterModel version.")
        coeffs = []
        for length in lengths[:4]:
            mem_io = io.BytesIO()
            mem_io.write(byte_repr[size : size + length])
            mem_io.seek(0)
            coeffs.append(numpy.load(mem_io))
            size += length
        if all(length == 0 for length in lengths[4:]):
            ports = None
        else:
            ports = []
            for length in lengths[4:]:
                ports.append(byte_repr[size : size + length].decode("utf8"))
                size += length
        return cls(*coeffs, ports)


class PolarizationBeamSplitterModel(Model):
    r"""Data model for a 3-port polarization beam splitter.

    The S matrix, considering no mode mixing, is represented by:

    .. math:: S = \begin{bmatrix}
                     r_0  &  t_1  &  t_2  \\
                     t_1  &  r_1  &   i   \\
                     t_2  &   i   &  r_2  \\
                  \end{bmatrix}

    The defaults assume that the 3 ports support up to 2 modes. More modes
    can be supported by extending the coefficients (see note below).

    Args:
        t1: Transmission coefficient to the first output port.
        t2: Transmission coefficient to the second output port.
        i: Leakage (isolation) coefficient between outputs.
        r0: Reflection coefficient for the input port.
        r1: Reflection coefficient for the first output port.
        r2: Reflection coefficient for the second output port.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.

    Notes:
        For multimode ports, a sequence of coefficients must be used, and
        mixed-mode coefficients are 0. Dispersion can be included in the
        model by setting the coefficients to an :class:`Interpolator` (with
        multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        *,
        t1: _ComplexCoeff = (1, 0),
        t2: _ComplexCoeff = (0, 1),
        i: _ComplexCoeff = (0, 0),
        r0: _ComplexCoeff = (0, 0),
        r1: _ComplexCoeff = (0, 0),
        r2: _ComplexCoeff = (0, 0),
        ports: pft.annotate(Sequence[str], minItems=3, maxItems=3) | None = None,
    ) -> None:
        super().__init__(
            t1=_ensure_correct_shape(t1),
            t2=_ensure_correct_shape(t2),
            i=_ensure_correct_shape(i),
            r0=_ensure_correct_shape(r0),
            r1=_ensure_correct_shape(r1),
            r2=_ensure_correct_shape(r2),
            ports=ports,
        )
        if ports is not None and len(ports) != 3:
            raise TypeError(
                f"PolarizationBeamSplitterModel can only be used on components with 3 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "pbs"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = width * 8

        p1 = [(0, 0), (0.25 * length, 0), (0.75 * length, 1.5 * width), (length, 1.5 * width)]
        p2 = [(0, 0), (length, 0)]

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            polygons = boolean(
                Path(p1[0], w, g).segment(p1[1:]), Path(p2[0], w, g).segment(p2[1:]), "+"
            )
            component.add(layer, *polygons)

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 3
        component.add_port(Port(p1[0], 0, port_spec), port_names[0])
        component.add_port(Port(p2[-1], 180, port_spec), port_names[1])
        component.add_port(Port(p1[-1], 180, port_spec), port_names[2])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 3:
            raise RuntimeError(
                f"PolarizationBeamSplitterModel can only be used on components with 3 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in PolarizationBeamSplitterModel match the "
                f"{classification} port names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"PolarizationBeamSplitterModel requires that all component ports have the same "
                f"number of modes. Ports from '{component.name}' support different numbers of "
                f"modes."
            )

        t1 = _sample(component.name, "t1", p["t1"], frequencies, num_modes)
        t2 = _sample(component.name, "t2", p["t2"], frequencies, num_modes)
        i = _sample(component.name, "i", p["i"], frequencies, num_modes)
        r0 = _sample(component.name, "r0", p["r0"], frequencies, num_modes)
        r1 = _sample(component.name, "r1", p["r1"], frequencies, num_modes)
        r2 = _sample(component.name, "r2", p["r2"], frequencies, num_modes)

        s = (
            (r0, t1, t2),
            (t1, r1, i),
            (t2, i, r2),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)


class PolarizationSplitterRotatorModel(Model):
    r"""Data model for a polarization splitter rotator.

    Two types of PSR models are supported: a 4-port model that assumes a
    2-mode input port and 2 single-mode outputs; and a 6-port model that
    assumes all 3 ports support 2 modes.

    The full 6-port S matrix is represented by the usual coefficients:

    .. math:: S_{6p} = \begin{bmatrix}
                          s_{00} & s_{01} & \cdots & s_{05} \\
                          s_{01} & s_{11} & \cdots & s_{15} \\
                          \vdots & \vdots & \ddots & \vdots \\
                          s_{05} & s_{15} & \cdots & s_{55} \\
                       \end{bmatrix}

    The 4-port version drops the coefficients related to the unused mode in
    the output ports. Using ``output_mode = 0`` (default):

    .. math:: S_{4p} = \begin{bmatrix}
                          s_{00} & s_{01} & s_{02} & s_{04} \\
                          s_{01} & s_{11} & s_{12} & s_{14} \\
                          s_{02} & s_{12} & s_{22} & s_{24} \\
                          s_{04} & s_{14} & s_{24} & s_{44} \\
                       \end{bmatrix}

    and using ``output_mode = 1``:

    .. math:: S'_{4p} = \begin{bmatrix}
                          s_{00} & s_{01} & s_{03} & s_{05} \\
                          s_{01} & s_{11} & s_{13} & s_{15} \\
                          s_{03} & s_{13} & s_{33} & s_{35} \\
                          s_{05} & s_{15} & s_{35} & s_{55} \\
                       \end{bmatrix}

    Args:
        s00: Reflection for first mode on input port.
        s01: Inter-mode reflection for input port.
        s02: Transmission for first mode on input port to first mode on
          first output port.
        s03: Transmission for first mode on input port to second mode on
          first output port.
        s04: Transmission for first mode on input port to first mode on
          second output port.
        s05: Transmission for first mode on input port to second mode on
          second output port.
        s11: Reflection for second mode on input port.
        s12: Transmission for second mode on input port to first mode on
          first output port.
        s13: Transmission for second mode on input port to second mode on
          first output port.
        s14: Transmission for second mode on input port to first mode on
          second output port.
        s15: Transmission for second mode on input port to second mode on
          second output port.
        s22: Reflection for first mode on first output port.
        s23: Inter-mode reflection for the first output port.
        s24: Leakage (isolation) between the first mode on the first output
          port and the first mode on the second output port.
        s25: Leakage (isolation) between the first mode on the first output
          port and the second mode on the second output port.
        s33: Reflection for second mode on first output port.
        s34: Leakage (isolation) between the second mode on the first output
          port and the first mode on the second output port.
        s35: Leakage (isolation) between the second mode on the first output
          port and the second mode on the second output port.
        s44: Reflection for first mode on second output port.
        s45: Inter-mode reflection for the second output port.
        s55: Reflection for second mode on second output port.
        output_mode: Mode number used in output ports in the 4-port version.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.

    Notes:
        Dispersion can be included in the model by setting the coefficients
        to :class:`Interpolator` objects or to 1D arrays with the length of
        the frequencies vector to be used in the computation.
    """

    def __init__(
        self,
        *,
        s00: _ComplexCoeff1D | Interpolator = 0,
        s01: _ComplexCoeff1D | Interpolator = 0,
        s02: _ComplexCoeff1D | Interpolator = 1,
        s03: _ComplexCoeff1D | Interpolator = 0,
        s04: _ComplexCoeff1D | Interpolator = 0,
        s05: _ComplexCoeff1D | Interpolator = 0,
        s11: _ComplexCoeff1D | Interpolator = 0,
        s12: _ComplexCoeff1D | Interpolator = 0,
        s13: _ComplexCoeff1D | Interpolator = 0,
        s14: _ComplexCoeff1D | Interpolator = 1,
        s15: _ComplexCoeff1D | Interpolator = 0,
        s22: _ComplexCoeff1D | Interpolator = 0,
        s23: _ComplexCoeff1D | Interpolator = 0,
        s24: _ComplexCoeff1D | Interpolator = 0,
        s25: _ComplexCoeff1D | Interpolator = 0,
        s33: _ComplexCoeff1D | Interpolator = 0,
        s34: _ComplexCoeff1D | Interpolator = 0,
        s35: _ComplexCoeff1D | Interpolator = 0,
        s44: _ComplexCoeff1D | Interpolator = 0,
        s45: _ComplexCoeff1D | Interpolator = 0,
        s55: _ComplexCoeff1D | Interpolator = 0,
        output_mode: Literal[0, 1] = 0,
        ports: pft.annotate(Sequence[str], minItems=3, maxItems=3) | None = None,
    ) -> None:
        super().__init__(
            s00=_ensure_correct_shape(s00, ndims=1),
            s01=_ensure_correct_shape(s01, ndims=1),
            s02=_ensure_correct_shape(s02, ndims=1),
            s03=_ensure_correct_shape(s03, ndims=1),
            s04=_ensure_correct_shape(s04, ndims=1),
            s05=_ensure_correct_shape(s05, ndims=1),
            s11=_ensure_correct_shape(s11, ndims=1),
            s12=_ensure_correct_shape(s12, ndims=1),
            s13=_ensure_correct_shape(s13, ndims=1),
            s14=_ensure_correct_shape(s14, ndims=1),
            s15=_ensure_correct_shape(s15, ndims=1),
            s22=_ensure_correct_shape(s22, ndims=1),
            s23=_ensure_correct_shape(s23, ndims=1),
            s24=_ensure_correct_shape(s24, ndims=1),
            s25=_ensure_correct_shape(s25, ndims=1),
            s33=_ensure_correct_shape(s33, ndims=1),
            s34=_ensure_correct_shape(s34, ndims=1),
            s35=_ensure_correct_shape(s35, ndims=1),
            s44=_ensure_correct_shape(s44, ndims=1),
            s45=_ensure_correct_shape(s45, ndims=1),
            s55=_ensure_correct_shape(s55, ndims=1),
            output_mode=int(output_mode),
            ports=ports,
        )
        if ports is not None and len(ports) != 3:
            raise TypeError(
                f"PolarizationSplitterRotatorModel can only be used on components with 3 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        output_port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            output_port_spec: Port specification used for the output ports in
              the component. If ``None``, use the same as ``port_spec``.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        # TODO: Add PSR icon
        component.properties.__thumbnail__ = "y-splitter"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")
        if isinstance(output_port_spec, str):
            name = output_port_spec
            output_port_spec = component.technology.ports.get(output_port_spec)
            if output_port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")
        elif output_port_spec is None:
            output_port_spec = port_spec

        width = max(port_spec.width, output_port_spec.width)
        length = width * 8

        p0 = [(0, 0), (0.5 * length, 0)]
        p1 = [(0.5 * length, 0), (length, 0)]
        p2 = [(0.25 * length, 1.5 * width), (0.75 * length, 1.5 * width), (length, 1.5 * width)]

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            component.add(layer, Path(p0[0], w, g).segment(p0[1:]))

        profiles = output_port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            component.add(
                layer,
                Path(p1[0], w, g).segment(p1[1:]),
                Path(p2[0], 0, g - 0.5 * width).segment(p2[1], w, g).segment(p2[2]),
            )

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 3
        component.add_port(Port(p0[0], 0, port_spec), port_names[0])
        component.add_port(Port(p1[-1], 180, output_port_spec), port_names[1])
        component.add_port(Port(p2[-1], 180, output_port_spec), port_names[2])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 3:
            raise RuntimeError(
                f"PolarizationSplitterRotatorModel can only be used on components with 3 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        p = self.parametric_kwargs

        names = p["ports"]
        output_mode = p["output_mode"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in PolarizationSplitterRotatorModel match the "
                f"{classification} port names in component '{component.name}'."
            )
        p0, p1, p2 = names

        input_modes = component_ports[p0].num_modes
        output_modes = component_ports[p1].num_modes
        if not (
            input_modes == 2
            and output_modes in (1, 2)
            and output_modes == component_ports[p2].num_modes
        ):
            raise RuntimeError(
                f"PolarizationSplitterRotatorModel requires 2 modes in the first port '{p0}', and "
                f"the same number of modes (1 or 2) for ports '{p1}' and '{p2}'."
            )

        shape = (len(frequencies),)
        s00 = p["s00"]
        s00 = (
            s00(frequencies)
            if isinstance(s00, Interpolator)
            else numpy.array(numpy.broadcast_to(s00, shape))
        )
        s01 = p["s01"]
        s01 = (
            s01(frequencies)
            if isinstance(s01, Interpolator)
            else numpy.array(numpy.broadcast_to(s01, shape))
        )
        s02 = p["s02"]
        s02 = (
            s02(frequencies)
            if isinstance(s02, Interpolator)
            else numpy.array(numpy.broadcast_to(s02, shape))
        )
        s03 = p["s03"]
        s03 = (
            s03(frequencies)
            if isinstance(s03, Interpolator)
            else numpy.array(numpy.broadcast_to(s03, shape))
        )
        s04 = p["s04"]
        s04 = (
            s04(frequencies)
            if isinstance(s04, Interpolator)
            else numpy.array(numpy.broadcast_to(s04, shape))
        )
        s05 = p["s05"]
        s05 = (
            s05(frequencies)
            if isinstance(s05, Interpolator)
            else numpy.array(numpy.broadcast_to(s05, shape))
        )
        s11 = p["s11"]
        s11 = (
            s11(frequencies)
            if isinstance(s11, Interpolator)
            else numpy.array(numpy.broadcast_to(s11, shape))
        )
        s12 = p["s12"]
        s12 = (
            s12(frequencies)
            if isinstance(s12, Interpolator)
            else numpy.array(numpy.broadcast_to(s12, shape))
        )
        s13 = p["s13"]
        s13 = (
            s13(frequencies)
            if isinstance(s13, Interpolator)
            else numpy.array(numpy.broadcast_to(s13, shape))
        )
        s14 = p["s14"]
        s14 = (
            s14(frequencies)
            if isinstance(s14, Interpolator)
            else numpy.array(numpy.broadcast_to(s14, shape))
        )
        s15 = p["s15"]
        s15 = (
            s15(frequencies)
            if isinstance(s15, Interpolator)
            else numpy.array(numpy.broadcast_to(s15, shape))
        )
        s22 = p["s22"]
        s22 = (
            s22(frequencies)
            if isinstance(s22, Interpolator)
            else numpy.array(numpy.broadcast_to(s22, shape))
        )
        s23 = p["s23"]
        s23 = (
            s23(frequencies)
            if isinstance(s23, Interpolator)
            else numpy.array(numpy.broadcast_to(s23, shape))
        )
        s24 = p["s24"]
        s24 = (
            s24(frequencies)
            if isinstance(s24, Interpolator)
            else numpy.array(numpy.broadcast_to(s24, shape))
        )
        s25 = p["s25"]
        s25 = (
            s25(frequencies)
            if isinstance(s25, Interpolator)
            else numpy.array(numpy.broadcast_to(s25, shape))
        )
        s33 = p["s33"]
        s33 = (
            s33(frequencies)
            if isinstance(s33, Interpolator)
            else numpy.array(numpy.broadcast_to(s33, shape))
        )
        s34 = p["s34"]
        s34 = (
            s34(frequencies)
            if isinstance(s34, Interpolator)
            else numpy.array(numpy.broadcast_to(s34, shape))
        )
        s35 = p["s35"]
        s35 = (
            s35(frequencies)
            if isinstance(s35, Interpolator)
            else numpy.array(numpy.broadcast_to(s35, shape))
        )
        s44 = p["s44"]
        s44 = (
            s44(frequencies)
            if isinstance(s44, Interpolator)
            else numpy.array(numpy.broadcast_to(s44, shape))
        )
        s45 = p["s45"]
        s45 = (
            s45(frequencies)
            if isinstance(s45, Interpolator)
            else numpy.array(numpy.broadcast_to(s45, shape))
        )
        s55 = p["s55"]
        s55 = (
            s55(frequencies)
            if isinstance(s55, Interpolator)
            else numpy.array(numpy.broadcast_to(s55, shape))
        )

        if output_modes == 2:
            s = (
                (s00, s01, s02, s03, s04, s05),
                (s01, s11, s12, s13, s14, s15),
                (s02, s12, s22, s23, s24, s25),
                (s03, s13, s23, s33, s34, s35),
                (s04, s14, s24, s34, s44, s45),
                (s05, s15, s25, s35, s45, s55),
            )
            names = [f"{p0}@0", f"{p0}@1", f"{p1}@0", f"{p1}@1", f"{p2}@0", f"{p2}@1"]
        else:
            if output_mode == 0:
                s = (
                    (s00, s01, s02, s04),
                    (s01, s11, s12, s14),
                    (s02, s12, s22, s24),
                    (s04, s14, s24, s44),
                )
            else:
                s = (
                    (s00, s01, s03, s05),
                    (s01, s11, s13, s15),
                    (s03, s13, s33, s35),
                    (s05, s15, s35, s55),
                )
            names = [f"{p0}@0", f"{p0}@1", f"{p1}@{output_mode}", f"{p2}@{output_mode}"]
        elements = {
            (port_in, port_out): s[j][i]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
        }
        return SMatrix(frequencies, elements, component_ports)


class DirectionalCouplerModel(Model):
    r"""Data model for a 4-port directional coupler.

    .. math:: S = \begin{bmatrix}
                     r   &  i   &  t'  &  c'  \\
                     i   &  r   &  c'  &  t'  \\
                     t'  &  c'  &  r   &  i   \\
                     c'  &  t'  &  i   &  r   \\
                  \end{bmatrix}


    with coefficients:

    .. math::

       t' &= t e^{j \phi}

       c' &= c e^{j \phi}

       \phi &= \frac{2 \pi l_p}{c_0}
         [n_\text{eff} f_0 + n_\text{group} (f - f_0)]

    Args:
        t: Transmission coefficient. If ``None``, it is calculated based on
          the magnitude of the other coefficients and the phase of ``c``
          plus 90°.
        c: Coupling coefficient.
        i: Leakage (isolation) coefficient.
        r: Reflection coefficient.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.
        propagation_length: Propagation length :math:`l_p` for dispersion
          modeling.
        n_eff: Effective refractive index for dispersion modeling.
        n_group: Group index. If ``None``, the value of ``n_eff`` is used.
        reference_frequency: Reference frequency :math:`f_0` for dispersion
          calculation. If ``None``, the central frequency is used.

    Notes:
        For multimode ports, a sequence of coefficients must be used, and
        mixed-mode coefficients are 0. Dispersion can be included in the
        model by setting the coefficients to an :class:`Interpolator` (with
        multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        t: _ComplexCoeff | Interpolator | None = None,
        c: _ComplexCoeff | Interpolator = -1j * 2**-0.5,
        i: _ComplexCoeff | Interpolator = 0,
        r: _ComplexCoeff | Interpolator = 0,
        ports: pft.annotate(Sequence[str], minItems=4, maxItems=4) | None = None,
        *,
        propagation_length: pft.annotate(float, units="μm") = 0.0,
        n_eff: _ComplexCoeff | Interpolator = 0.0,
        n_group: _FloatCoeff | None = None,
        reference_frequency: pft.Frequency | None = None,
    ) -> None:
        super().__init__(
            t=t,
            c=_ensure_correct_shape(c),
            i=_ensure_correct_shape(i),
            r=_ensure_correct_shape(r),
            ports=ports,
            propagation_length=propagation_length,
            n_eff=_ensure_correct_shape(n_eff),
            n_group=n_group,
            reference_frequency=reference_frequency,
        )
        if ports is not None and len(ports) != 4:
            raise TypeError(
                f"DirectionalCouplerModel can only be used on components with 4 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "dc"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = abs(self.parametric_kwargs["propagation_length"])
        if length == 0.0:
            length = width * 8

        p1 = [
            (0, -0.75 * width),
            (0.25 * length, -0.75 * width),
            (0.75 * length, 0.75 * width),
            (length, 0.75 * width),
        ]
        p2 = [(x, -y) for x, y in p1]

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            polygons = boolean(
                Path(p1[0], w, g).segment(p1[1:]), Path(p2[0], w, g).segment(p2[1:]), "+"
            )
            component.add(layer, *polygons)

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 4
        component.add_port(Port(p1[0], 0, port_spec), port_names[0])
        component.add_port(Port(p2[0], 0, port_spec), port_names[1])
        component.add_port(Port(p2[-1], 180, port_spec), port_names[2])
        component.add_port(Port(p1[-1], 180, port_spec), port_names[3])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 4:
            raise RuntimeError(
                f"DirectionalCouplerModel can only be used on components with 4 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in DirectionalCouplerModel match the "
                f"{classification} port names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"DirectionalCouplerModel requires that all component ports have the same number "
                f"of modes. Ports from '{component.name}' support different numbers of modes."
            )

        lp = _ensure_correct_shape(p["propagation_length"])

        f0 = p["reference_frequency"]
        if f0 is None:
            f0 = 0.5 * (frequencies.min() + frequencies.max())

        n_eff = _sample(component.name, "n_eff", p["n_eff"], frequencies, num_modes)
        n_group = p["n_group"]
        if n_group is None:
            n_group = n_eff
        else:
            n_group = _ensure_correct_shape(n_group)

        n_f = (n_eff - n_group) * f0 + n_group * frequencies
        phase = numpy.exp(2j * numpy.pi * lp * n_f / C_0)

        c = _sample(component.name, "c", p["c"], frequencies, num_modes) * phase
        i = _sample(component.name, "i", p["i"], frequencies, num_modes)
        r = _sample(component.name, "r", p["r"], frequencies, num_modes)

        t = p["t"]
        if t is None:
            t_mag = numpy.sqrt(1 - numpy.abs(c) ** 2 - numpy.abs(i) ** 2 - numpy.abs(r) ** 2)
            t = 1j * numpy.exp(1j * numpy.angle(c)) * t_mag
        else:
            t = (
                _sample(component.name, "t", _ensure_correct_shape(t), frequencies, num_modes)
                * phase
            )

        s = (
            (r, i, t, c),
            (i, r, c, t),
            (t, c, r, i),
            (c, t, i, r),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "DirectionalCouplerModel":
        """De-serialize this model."""
        size = struct.calcsize("<B8Q")
        version, *lengths = struct.unpack("<B8Q", byte_repr[:size])
        if version != 0:
            raise RuntimeError("Unsuported DirectionalCouplerModel version.")
        coeffs = []
        for length in lengths[:4]:
            mem_io = io.BytesIO()
            mem_io.write(byte_repr[size : size + length])
            mem_io.seek(0)
            coeffs.append(numpy.load(mem_io))
            size += length
        if all(length == 0 for length in lengths[4:]):
            ports = None
        else:
            ports = []
            for length in lengths[4:]:
                ports.append(byte_repr[size : size + length].decode("utf8"))
                size += length
        return cls(*coeffs, ports)


class CrossingModel(Model):
    r"""Data model for a 4-port waveguide crossing.

    .. math:: S = \begin{bmatrix}
                     r  &  x  &  t  &  x  \\
                     x  &  r  &  x  &  t  \\
                     t  &  x  &  r  &  x  \\
                     x  &  t  &  x  &  r  \\
                  \end{bmatrix} e^{j \phi}


    with dispersion modeled by:

    .. math:: \phi = \frac{2 \pi l_p}{c_0}
         [n_\text{eff} f_0 + n_\text{group} (f - f_0)]

    Args:
        t: Transmission coefficient.
        x: Cross-coupling coefficient.
        r: Reflection coefficient.
        propagation_length: Propagation length :math:`l_p` for dispersion
          modeling.
        n_eff: Effective refractive index for dispersion modeling.
        n_group: Group index. If ``None``, the value of ``n_eff`` is used.
        reference_frequency: Reference frequency :math:`f_0` for dispersion
          calculation. If ``None``, the central frequency is used.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.

    Notes:
        For multimode ports, a sequence of coefficients must be used, and
        mixed-mode coefficients are 0. Dispersion can be included in the
        model by setting the coefficients to an :class:`Interpolator` (with
        multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        *,
        t: _ComplexCoeff | Interpolator = 1.0,
        x: _ComplexCoeff | Interpolator = 0.0,
        r: _ComplexCoeff | Interpolator = 0.0,
        propagation_length: pft.annotate(float, units="μm") = 0.0,
        n_eff: _ComplexCoeff | Interpolator = 0.0,
        n_group: _FloatCoeff | None = None,
        reference_frequency: pft.Frequency | None = None,
        ports: pft.annotate(Sequence[str], minItems=4, maxItems=4) | None = None,
    ) -> None:
        super().__init__(
            t=_ensure_correct_shape(t),
            x=_ensure_correct_shape(x),
            r=_ensure_correct_shape(r),
            ports=ports,
            propagation_length=propagation_length,
            n_eff=_ensure_correct_shape(n_eff),
            n_group=n_group,
            reference_frequency=reference_frequency,
        )
        if ports is not None and len(ports) != 4:
            raise TypeError(
                f"CrossingModel can only be used on components with 4 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "crossing"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = abs(self.parametric_kwargs["propagation_length"])
        if length == 0.0:
            length = width * 8

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            polygons = boolean(
                Path((-length / 2, 0), w, g).segment((length / 2, 0)),
                Path((0, -length / 2), w, g).segment((0, length / 2)),
                "+",
            )
            component.add(layer, *polygons)

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 4
        component.add_port(Port((-length / 2, 0), 0, port_spec), port_names[0])
        component.add_port(Port((0, -length / 2), 90, port_spec), port_names[1])
        component.add_port(Port((length / 2, 0), 180, port_spec), port_names[2])
        component.add_port(Port((0, length / 2), 270, port_spec), port_names[3])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 4:
            raise RuntimeError(
                f"DirectionalCouplerModel can only be used on components with 4 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports."
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in DirectionalCouplerModel match the "
                f"{classification} port names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"DirectionalCouplerModel requires that all component ports have the same number "
                f"of modes. Ports from '{component.name}' support different numbers of modes."
            )

        lp = _ensure_correct_shape(p["propagation_length"])

        f0 = p["reference_frequency"]
        if f0 is None:
            f0 = 0.5 * (frequencies.min() + frequencies.max())

        n_eff = _sample(component.name, "n_eff", p["n_eff"], frequencies, num_modes)
        n_group = p["n_group"]
        if n_group is None:
            n_group = n_eff
        else:
            n_group = _ensure_correct_shape(n_group)

        n_f = (n_eff - n_group) * f0 + n_group * frequencies
        phase = numpy.exp(2j * numpy.pi * lp * n_f / C_0)

        t = _sample(component.name, "t", p["t"], frequencies, num_modes) * phase
        x = _sample(component.name, "x", p["x"], frequencies, num_modes) * phase
        r = _sample(component.name, "r", p["r"], frequencies, num_modes) * phase

        s = (
            (r, x, t, x),
            (x, r, x, t),
            (t, x, r, x),
            (x, t, x, r),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)


class _WaveguideModelRunner:
    def __init__(self, runner, free_space_phase, frequencies, ports) -> None:
        self.runner = runner
        self.free_space_phase = free_space_phase
        self.frequencies = frequencies
        self.ports = ports
        self._s_matrix = None

    @property
    def status(self):
        return self.runner.status

    @property
    def s_matrix(self):
        if self._s_matrix is None:
            data = self.runner.data
            num_modes = next(iter(self.ports.values())).num_modes
            n_complex = data.n_complex.values.T
            s = numpy.exp(1j * self.free_space_phase * n_complex)

            elements = {
                (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[mode]
                for port_in in self.ports
                for port_out in self.ports
                for mode in range(num_modes)
                if port_in != port_out
            }

            self._s_matrix = SMatrix(self.frequencies, elements, self.ports)

        return self._s_matrix


class WaveguideModel(Model):
    r"""Data model for straight waveguides.

    The component is expected to have 2 ports with identical profiles. The S
    matrix is zero for all reflection or mixed-mode coefficients. Same-mode
    transmission coefficients are modeled by:

    .. math:: S_{jk} = \exp(i 2 \pi f n_c L / c₀)

    with :math:`n_c` the complex effective index for the port profile modes,
    and :math:`L` the waveguide length.

    Args:
        n_complex: Waveguide complex effective index. For multimode models,
          a sequence of indices must be provided, one for each mode. If set
          to ``None``, automatic computation is performed by mode-solving
          the first component port. If desired, the port specification of
          the component port can be overridden by setting ``n_complex`` to
          ``"cross-section"`` (uses :func:`Component.slice_profile`) or to
          a :class:`PortSpec` object.
        length: Physical length of the waveguide. If not provided, the
          length is measured by :func:`route_length` or ports distance.
        mesh_refinement: Minimal number of mesh elements per wavelength used
          for mode solving.
        verbose: Flag setting the verbosity of mode solver runs.

    Note:
        Dispersion can be included in the model by setting ``n_complex`` to
        an :class:`Interpolator` (with multiple values for multimode ports),
        or a 2D array with shape (M, N), in which M is the number of modes
        in the waveguide, and N the length of the frequency sequence used in
        the S matrix computation.

    See also:
        `Mach-Zehnder Interferometer
        <../examples/MZI.ipynb#Semi-Analytic-Design-Exploration>`__
    """

    def __init__(
        self,
        n_complex: _ComplexCoeff | Interpolator | PortSpec | Literal["cross-section"] | None = None,
        length: pft.Coordinate | None = None,
        mesh_refinement: pft.PositiveFloat | None = None,
        verbose: bool = True,
    ) -> None:
        super().__init__(
            n_complex=n_complex,
            length=length,
            mesh_refinement=mesh_refinement,
            verbose=verbose,
        )
        self.n_complex = (
            _ensure_correct_shape(n_complex)
            if self._classify_n_complex(n_complex) in (numpy.ndarray, Interpolator)
            else n_complex
        )
        self.length = length
        self.mesh_refinement = mesh_refinement
        self.verbose = verbose

    @classmethod
    def _classify_n_complex(cls, n_complex):
        if n_complex is None:
            return None
        elif isinstance(n_complex, str):
            if n_complex == "cross-section":
                return str
            raise ValueError(
                "'n_complex' must be a scalar, array, PortSpec object, or the string "
                "'cross-section'. The string {n_complex!r} is not valid."
            )
        elif isinstance(n_complex, PortSpec):
            return PortSpec
        elif isinstance(n_complex, Interpolator):
            return Interpolator
        else:
            return numpy.ndarray

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "wg"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = self.length if self.length and self.length > 0 else width * 8

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            component.add(layer, Path((0, 0), w, g).segment((length, 0)))

        _add_bb_text(component, width)

        component.add_port((Port((0, 0), 0, port_spec), Port((length, 0), 180, port_spec)))
        component.add_model(self, model_name)
        return component

    @cache_s_matrix
    def start(
        self,
        component: Component,
        frequencies: Sequence[float],
        verbose: bool | None = None,
        cost_estimation: bool = False,
        **kwargs: Any,
    ) -> SMatrix | _WaveguideModelRunner:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            verbose: If set, overrides the model's `verbose` attribute.
            cost_estimation: If set, simulations are uploaded, but not
              executed. S matrix may *not* be computed.
            **kwargs: Unused.

        Returns:
           Result object with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 2:
            raise RuntimeError(
                f"WaveguideModel can only be used on components with 2 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports.",
            )

        port_names = sorted(component_ports)
        port0 = component_ports[port_names[0]]
        port1 = component_ports[port_names[1]]

        if not isinstance(port0, Port) or not isinstance(port1, Port):
            raise RuntimeError(
                "WaveguideModel can only be used on components with planar ports (Port instances)."
            )

        if not port0.can_connect_to(port1):
            raise RuntimeError(
                "WaveguideModel can only be used on components with 2 ports with matching path "
                "profiles."
            )

        length = self.length
        if length is None:
            length = 0
            for _, _, layer in port0.spec.path_profiles_list():
                length = max(length, route_length(component, layer))
            if length <= 0:
                length = numpy.sqrt(numpy.sum((port0.center - port1.center) ** 2))

        frequencies = numpy.array(frequencies, dtype=float, ndmin=1)

        if verbose is None:
            verbose = self.verbose

        n_type = self._classify_n_complex(self.n_complex)
        if n_type in (numpy.ndarray, Interpolator):
            num_modes = port0.num_modes
            coeff = (2.0j * numpy.pi / C_0) * _sample(
                component.name, "n_complex", self.n_complex, frequencies, num_modes
            )

            t = numpy.exp(coeff * length * frequencies)
            elements = {
                (f"{port_in}@{mode}", f"{port_out}@{mode}"): t[mode]
                for port_in, port_out in [port_names, (port_names[1], port_names[0])]
                for mode in range(num_modes)
            }
            return SMatrix(frequencies, elements, component_ports)

        free_space_phase = 2.0 * numpy.pi / C_0 * length * frequencies
        for port in component_ports.values():
            if port.spec.polarization != "":
                port.spec = port.spec.copy()
                port.spec.polarization = ""
                port.spec.num_modes += port.spec.added_solver_modes
                port.spec.added_solver_modes = 0

        ms_port = port0.copy(True)
        if n_type is PortSpec:
            ms_port.spec = libcopy.deepcopy(self.n_complex)
        elif n_type is str:
            direction = int((ms_port.input_direction + 45) // 90) % 4
            angle = ms_port.input_direction - 90 * direction
            axis = "x" if direction % 2 == 0 else "y"

            x_length = ms_port.spec.width + 2 * config.tolerance
            x_center = ms_port.center.copy()
            x_center[direction % 2] += config.grid * 2 * (1 - 2 * (direction // 2))
            x_comp = Component().add(
                Reference(
                    Component().add(Reference(component, -ms_port.center)), ms_port.center, -angle
                )
            )
            ms_port.spec.path_profiles = x_comp.slice_profile(axis, x_center, x_length)
        runner = _ModeSolverRunner(
            ms_port,
            frequencies,
            self.mesh_refinement,
            component.technology,
            cost_estimation=cost_estimation,
            verbose=verbose,
        )
        return _WaveguideModelRunner(runner, free_space_phase, frequencies, component_ports)

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "WaveguideModel":
        """De-serialize this model."""
        version = byte_repr[0]
        if version == 2:
            return cls(**dict(_from_bytes(byte_repr[1:])))
        elif version == 1:
            head_len = struct.calcsize("<BB2d")
            flags, length, mesh_refinement = struct.unpack("<B2d", byte_repr[1:head_len])
            verbose = (flags & 0x01) > 0
            lenght_is_none = (flags & 0x02) > 0
            n_type = {0x00: None, 0x04: str, 0x08: PortSpec, 0x0C: numpy.ndarray}.get(flags & 0x0C)
        elif version == 0:
            head_len = struct.calcsize("<B3?2d")
            n_complex_is_none, lenght_is_none, verbose, length, mesh_refinement = struct.unpack(
                "<3?2d", byte_repr[1:head_len]
            )
            n_type = None if n_complex_is_none else numpy.ndarray
        else:
            raise RuntimeError(
                "This WaveguideModel seems to have been created by a more recent version of "
                "PhotonForge and it is not supported by the this version."
            )

        if mesh_refinement <= 0:
            mesh_refinement = None

        if lenght_is_none:
            length = None

        n_complex = None
        if n_type is PortSpec:
            kwds = json.loads(zlib.decompress(byte_repr[head_len:]).decode("utf-8"))
            profiles = kwds["path_profiles"]
            if isinstance(profiles, dict):
                kwds["path_profiles"] = {
                    k: (v["width"], v["offset"], v["layer"]) for k, v in profiles.items()
                }
            else:
                kwds["path_profiles"] = [(v["width"], v["offset"], v["layer"]) for v in profiles]
            if "electrical_spec" in kwds:
                # The 1e-5 factor is to fix a bug that existed in the json conversion
                kwds.update(
                    {k: numpy.array(v) * 1e-5 for k, v in kwds.pop("electrical_spec").items()}
                )
            n_complex = PortSpec(**kwds)
        elif n_type is str:
            n_complex = "cross-section"
        elif n_type is numpy.ndarray:
            mem_io = io.BytesIO()
            mem_io.write(byte_repr[head_len:])
            mem_io.seek(0)
            n_complex = numpy.load(mem_io)
            if version == 0:
                # Version 0 stored the transformed coefficient
                n_complex *= -0.5j / numpy.pi * C_0

        return cls(n_complex, length, mesh_refinement, verbose)


def _waveguide_transmission(
    frequencies,
    length,
    n_eff,
    n_group,
    dispersion,
    dispersion_slope,
    reference_frequency,
    propagation_loss,
    extra_loss,
    dn_dT,
    dL_dT,
    temperature,
    reference_temperature,
    voltage,
    v_piL,
    dloss_dv,
    dloss_dv2,
):
    if reference_frequency is None:
        reference_frequency = 0.5 * (frequencies.min() + frequencies.max())

    if n_group is None:
        n_group = n_eff
    else:
        n_group = _ensure_correct_shape(n_group)

    dT = temperature - reference_temperature
    n_eff = n_eff + dn_dT * dT
    propagation_loss = propagation_loss + dL_dT * dT
    total_loss = extra_loss + length * (
        propagation_loss + voltage * (dloss_dv + voltage * dloss_dv2)
    )

    w0 = 2 * numpy.pi * reference_frequency
    lda0 = C_0 / reference_frequency
    lda0_w0 = lda0 / w0

    beta0 = w0 * n_eff / C_0
    beta1 = n_group / C_0
    beta2 = -lda0_w0 * dispersion
    beta3 = lda0_w0**2 * (dispersion_slope + 2 * dispersion / lda0)
    dw = 2 * numpy.pi * (frequencies - reference_frequency)
    beta = beta0 + dw * (beta1 + dw * (beta2 / 2 + dw * beta3 / 6))

    if v_piL is None:
        beta_eo = 0.0
    else:
        beta_eo = numpy.pi * voltage / v_piL
    t = 10 ** (total_loss / -20) * numpy.exp(1j * (beta + beta_eo) * length)
    return t


class AnalyticWaveguideModel(Model):
    r"""Analytic model for waveguides, bends, and EO phase-shifters.

    This model for 2-port components includes dispersion and temperature
    sensitivity for single- and multi-mode waveguides. For each mode, the
    transmission between ports at frequency :math:`f` is:

    .. math::

       S_{12} &= S_{21} = 10^{-\frac{L}{20}} e^{j (\beta \ell + \phi_{eo})}

       L &= L_0 + \ell \left(L_p + \frac{{\rm d}L_p}{{\rm d}V} V
         + \frac{{\rm d}^2L_p}{{\rm d}V^2} V^2 \right)

       \beta &= \beta_0 + \beta_1 \Delta\omega
         + \frac{\beta_2}{2} \Delta\omega^2
         + \frac{\beta_3}{6} \Delta\omega^3

       \beta_0 &= \frac{\omega_0}{c_0} n_\text{eff}

       \beta_1 &= \frac{n_\text{group}}{c_0}

       \beta_2 &= -\frac{\lambda_0}{\omega_0} D

       \beta_3 &= \left(\frac{\lambda_0}{\omega_0}\right)^2
         \left(S + \frac{2}{\lambda_0} D\right)

       \phi_{eo} &= \frac{\pi V \ell}{V_{\pi L}}

    in which :math:`\lambda_0 = c_0 f_0^{-1}`, :math:`\omega_0 = 2 \pi f_0`,
    :math:`\Delta\omega = 2 \pi (f - f_0)`, and the temperature dependence
    is taken into account through:

    .. math::

       n_\text{eff}(T) &= n_\text{eff}(T_0)
         + \frac{{\rm d}n_\text{eff}}{{\rm d}T} (T - T_0)

       L_p(T) &= L_p(T_0) + \frac{{\rm d}L_p}{{\rm d}T} (T - T_0)


    Args:
        n_eff: Effective refractive index (loss can be included here by
          using complex values).
        length: Length :math:`\ell` of the waveguide. If not provided, the
          length is measured by :func:`route_length` or ports distance.
        propagation_loss: Propagation loss :math:`L_p`.
        extra_loss: Length-independent loss :math:`L_0`. This can be used,
          for example, to model bending losses.
        n_group: Group index. If ``None``, the value of ``n_eff`` is used.
        dispersion: Chromatic dispersion coefficient :math:`D`.
        dispersion_slope: Chromatic dispersion slope :math:`S`.
        reference_frequency: Reference frequency :math:`f_0` for dispersion
          coefficients. If ``None``, the central frequency is used.
        dn_dT: Temperature sensitivity for ``n_eff``.
        dL_dT: Temperature sensitivity for ``propagation_loss``.
        temperature: Operating temperature :math:`T`.
        reference_temperature: Reference temperature :math:`T_0`.
        voltage: Operating voltage :math:`V`.
        v_piL: Electro-optic phase coefficient :math:`V_{\pi L}`.
        dloss_dv: Linear voltage-dependent propagation loss coefficient.
        dloss_dv2: Quadratic voltage-dependent propagation loss coefficient.
    """

    def __init__(
        self,
        *,
        n_eff: complex | Sequence[complex] | Interpolator,
        length: pft.Coordinate | None = None,
        propagation_loss: pft.PropagationLoss | Sequence[pft.PropagationLoss] = 0.0,
        extra_loss: pft.Loss | Sequence[pft.Loss] = 0.0,
        n_group: float | Sequence[float] | None = None,
        dispersion: pft.Dispersion | Sequence[pft.Dispersion] = 0.0,
        dispersion_slope: pft.DispersionSlope | Sequence[pft.DispersionSlope] = 0.0,
        reference_frequency: pft.Frequency | None = None,
        dn_dT: pft.annotate(complex | Sequence[complex], label="dn/dT", units="1/K") = 0.0,
        dL_dT: pft.annotate(float | Sequence[float], label="dL/dT", units="dB/μm/K") = 0.0,
        temperature: pft.Temperature = 293.0,
        reference_temperature: pft.Temperature = 293.0,
        voltage: pft.Voltage = 0.0,
        v_piL: pft.annotate(float, label="VπL", units="V·μm") | None = None,
        dloss_dv: pft.annotate(float, label="dL/dV", units="dB/μm/V") = 0,
        dloss_dv2: pft.annotate(float, label="d²L/dV²", units="dB/μm/V²") = 0,
    ):
        super().__init__(
            length=length,
            n_eff=_ensure_correct_shape(n_eff),
            propagation_loss=_ensure_correct_shape(propagation_loss),
            extra_loss=_ensure_correct_shape(extra_loss),
            n_group=n_group,
            dispersion=_ensure_correct_shape(dispersion),
            dispersion_slope=_ensure_correct_shape(dispersion_slope),
            reference_frequency=reference_frequency,
            dn_dT=_ensure_correct_shape(dn_dT),
            dL_dT=_ensure_correct_shape(dL_dT),
            temperature=float(temperature),
            reference_temperature=float(reference_temperature),
            voltage=float(voltage),
            v_piL=v_piL,
            dloss_dv=dloss_dv,
            dloss_dv2=dloss_dv2,
        )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        p = self.parametric_kwargs

        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "wg" if p["v_piL"] is None else "eo-ps"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = p["length"]
        if length is None or length <= 0:
            length = width * 8

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            component.add(layer, Path((0, 0), w, g).segment((length, 0)))

        _add_bb_text(component, width)

        component.add_port((Port((0, 0), 0, port_spec), Port((length, 0), 180, port_spec)))

        component.add_model(self, model_name)
        return component

    def start(
        self,
        component: Component,
        frequencies: Sequence[pft.Frequency],
        temperature: pft.Temperature | None = None,
        voltage: pft.Voltage | None = None,
        **kwargs,
    ) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            temperature: Operating temperature override.
            voltage: Operating voltage override.
            **kwargs: Unused.

        Returns:
           Result object with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 2:
            raise RuntimeError(
                f"AnalyticWaveguideModel can only be used on components with 2 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports.",
            )

        port_names = sorted(component_ports)
        port0 = component_ports[port_names[0]]
        port1 = component_ports[port_names[1]]
        if port0.num_modes != port1.num_modes:
            raise RuntimeError(
                f"AnalyticWaveguideModel requires that all component ports have the same number of "
                f"modes. Ports from '{component.name}' support different numbers of modes."
            )

        frequencies = numpy.asarray(frequencies)

        p = self.parametric_kwargs

        length = p["length"]
        if length is None:
            length = 0
            for _, _, layer in port0.spec.path_profiles_list():
                length = max(length, route_length(component, layer))
            if length <= 0:
                length = numpy.sqrt(numpy.sum((port0.center - port1.center) ** 2))

        if temperature is None:
            temperature = p["temperature"]

        if voltage is None:
            voltage = p["voltage"]

        n_eff = _sample(component.name, "n_eff", p["n_eff"], frequencies, port0.num_modes)
        t = _waveguide_transmission(
            frequencies,
            length,
            n_eff,
            p["n_group"],
            p["dispersion"],
            p["dispersion_slope"],
            p["reference_frequency"],
            p["propagation_loss"],
            p["extra_loss"],
            p["dn_dT"],
            p["dL_dT"],
            temperature,
            p["reference_temperature"],
            voltage,
            p["v_piL"],
            p["dloss_dv"],
            p["dloss_dv2"],
        )

        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): t[mode]
            for port_in, port_out in [port_names, (port_names[1], port_names[0])]
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)


class AnalyticDirectionalCouplerModel(Model):
    r"""Analytic model for a 4-port directional coupler.

    The S matrix for the directional coupler for each mode is given by:

    .. math:: S = \begin{bmatrix}
                     r  &  i  &  t  &  c  \\
                     i  &  r  &  c  &  t  \\
                     t  &  c  &  r  &  i  \\
                     c  &  t  &  i  &  r  \\
                  \end{bmatrix}

    with coefficients:

    .. math::

       t &= \sqrt{1 - c_r} A e^{j \phi}

       c &= \sqrt{c_r} A e^{j (\phi + \Delta\phi)}

       c_r &= \sin^2\left(\frac{\pi l_i}{2 l_c}\right)

       A &= 10^{-\frac{L_\text{dB}}{20}}

       \phi &= \frac{2 \pi l_p}{c_0}
         [n_\text{eff} f_0 + n_\text{group} (f - f_0)]

    Args:
        interaction_length: Interaction length :math:`l_i`.
        coupling_length: Beat length :math:`l_c`.
        propagation_length: Propagation length :math:`l_p`. If ``None``, the
          value of ``interaction_length`` is used.
        cross_phase: Cross-port phase shift :math:`\Delta\phi`.
        insertion_loss: Insertion loss :math:`L_\text{dB}`.
        isolation: Leakage (isolation) coefficient :math:`i`.
        reflection: Reflection coefficient :math:`r`.
        n_eff: Effective refractive index.
        n_group: Group index. If ``None``, the value of ``n_eff`` is used.
        reference_frequency: Reference frequency :math:`f_0` for dispersion
          calculation. If ``None``, the frequency average is used.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.

    Notes:
        For multimode ports, a sequence of coefficients must be used, and
        mixed-mode coefficients are 0. Dispersion can be included in the
        model by setting the coefficients to an :class:`Interpolator` (with
        multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        *,
        interaction_length: float,
        coupling_length: pft.annotate(_FloatCoeff, units="μm"),
        propagation_length: pft.annotate(_FloatCoeff, units="μm") | None = None,
        cross_phase: pft.annotate(_FloatCoeff, units="°") = -90,
        insertion_loss: pft.annotate(_ComplexCoeff, units="dB") = 0.0,
        isolation: _ComplexCoeff | Interpolator = 0.0,
        reflection: _ComplexCoeff | Interpolator = 0.0,
        n_eff: _ComplexCoeff | Interpolator = 0.0,
        n_group: _FloatCoeff | None = None,
        reference_frequency: pft.Frequency | None = None,
        ports: pft.annotate(Sequence[str], minItems=4, maxItems=4) | None = None,
    ) -> None:
        super().__init__(
            interaction_length=float(interaction_length),
            coupling_length=_ensure_correct_shape(coupling_length),
            propagation_length=propagation_length,
            cross_phase=_ensure_correct_shape(cross_phase),
            insertion_loss=_ensure_correct_shape(insertion_loss),
            isolation=_ensure_correct_shape(isolation),
            reflection=_ensure_correct_shape(reflection),
            n_eff=_ensure_correct_shape(n_eff),
            n_group=n_group,
            reference_frequency=reference_frequency,
            ports=ports,
        )
        if ports is not None and len(ports) != 4:
            raise TypeError(
                f"AnalyticDirectionalCouplerModel can only be used on components with 4 ports. "
                f"Argument 'ports' has length {len(ports)}."
            )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "dc"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        length = self.parametric_kwargs["interaction_length"]
        if length <= 0:
            length = width * 8

        p1 = [
            (0, -0.75 * width),
            (0.25 * length, -0.75 * width),
            (0.75 * length, 0.75 * width),
            (length, 0.75 * width),
        ]
        p2 = [(x, -y) for x, y in p1]

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            polygons = boolean(
                Path(p1[0], w, g).segment(p1[1:]), Path(p2[0], w, g).segment(p2[1:]), "+"
            )
            component.add(layer, *polygons)

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 4
        component.add_port(Port(p1[0], 0, port_spec), port_names[0])
        component.add_port(Port(p2[0], 0, port_spec), port_names[1])
        component.add_port(Port(p2[-1], 180, port_spec), port_names[2])
        component.add_port(Port(p1[-1], 180, port_spec), port_names[3])

        component.add_model(self, model_name)
        return component

    def start(self, component: Component, frequencies: Sequence[float], **kwargs: Any) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            **kwargs: Unused.

        Returns:
           Model result with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 4:
            raise RuntimeError(
                f"AnalyticDirectionalCouplerModel can only be used on components with 4 ports. "
                f"'{component.name}' has {len(component_ports)} {classification} ports.",
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in AnalyticDirectionalCouplerModel match the "
                f"{classification} port names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"AnalyticDirectionalCouplerModel requires that all ports have the same number of "
                f"modes. Ports from '{component.name}' support different numbers of modes."
            )

        frequencies = numpy.asarray(frequencies)

        li = p["interaction_length"]
        lc = p["coupling_length"]
        lp = p["propagation_length"]
        if lp is None:
            lp = li
        else:
            lp = _ensure_correct_shape(lp)

        f0 = p["reference_frequency"]
        if f0 is None:
            f0 = frequencies.mean()

        n_eff = _sample(component.name, "n_eff", p["n_eff"], frequencies, num_modes)
        n_group = p["n_group"]
        if n_group is None:
            n_group = n_eff
        else:
            n_group = _ensure_correct_shape(n_group)

        phi = 2 * numpy.pi * lp * ((n_eff - n_group) * f0 + n_group * frequencies) / C_0
        cr = numpy.sin((numpy.pi * li) / (2 * lc)) ** 2
        a = 10 ** (-p["insertion_loss"] / 20)

        t = a * numpy.sqrt(1 - cr) * numpy.exp(1j * phi)
        c = a * numpy.sqrt(cr) * numpy.exp(1j * (phi + p["cross_phase"] / 180 * numpy.pi))

        i = _sample(component.name, "isolation", p["isolation"], frequencies, num_modes)
        r = _sample(component.name, "reflection", p["reflection"], frequencies, num_modes)

        s = (
            (r, i, t, c),
            (i, r, c, t),
            (t, c, r, i),
            (c, t, i, r),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
        }
        return SMatrix(frequencies, elements, component_ports)


class AnalyticMZIModel(Model):
    r"""Analytic model for a 4-port Mach-Zehnder interferometer.

    The S matrix for the MZI for each mode is given by:

    .. math::

       S_{31} &= \tau_1 t_1 \tau_2 + \kappa_1 t_2 \kappa_2

       S_{41} &= \tau_1 t_1 \kappa_2 + \kappa_1 t_2 \tau_2

       S_{32} &= \kappa_1 t_1 \tau_2 + \tau_1 t_2 \kappa_2

       S_{42} &= \kappa_1 t_1 \kappa_2 + \tau_1 t_2 \tau_2

    with remaining coefficients zero and transmissions $t_1$ and $t_2$
    calculated through an :class:`AnalyticWaveguideModel`.

    Args:
        n_eff1: Effective refractive index for the first arm (loss can be
          included here by using complex values).
        n_eff2: Effective refractive index for the second arm. If ``None``,
          defaults to ``n_eff1``.
        length1: Length of the first arm.
        length2: Length of the second arm. If ``None``, defaults to
          ``length1``.
        tau1: Transmission coefficient for the first coupler. If ``None``,
          it is calculated based on the magnitude of ``kappa1`` and its
          phase plus 90°.
        tau2: Transmission coefficient for the second coupler. If ``None``,
          it is calculated based on the magnitude of ``kappa2`` and its
          phase plus 90°.
        kappa1: Coupling coefficient for the first coupler.
        kappa2: Coupling coefficient for the second coupler.
        propagation_loss1: Propagation loss for the first arm.
        propagation_loss2: Propagation loss for the second arm.
        extra_loss1: Length-independent loss for the first arm.
        extra_loss2: Length-independent loss for the second arm.
        n_group1: Group index for the first arm.
        n_group2: Group index for the second arm.
        dispersion1: Chromatic dispersion coefficient for the first arm.
        dispersion2: Chromatic dispersion coefficient for the second arm.
        dispersion_slope1: Chromatic dispersion slope for the first arm.
        dispersion_slope2: Chromatic dispersion slope for the second arm.
        reference_frequency: Reference frequency for the dispersion
          coefficients. If ``None``, the central frequency is used.
        dn1_dT: Temperature sensitivity for ``n_eff1``.
        dn2_dT: Temperature sensitivity for ``n_eff2``.
        dL1_dT: Temperature sensitivity for ``propagation_loss1``.
        dL2_dT: Temperature sensitivity for ``propagation_loss2``.
        temperature1: Operating temperature for the first arm.
        temperature2: Operating temperature for the second arm.
        reference_temperature: Reference temperature.
        voltage1: Operating voltage for the first arm.
        voltage2: Operating voltage for the second arm.
        v_piL1: Electro-optic phase coefficient for the first arm.
        v_piL2: Electro-optic phase coefficient for the second arm.
        dloss_dv_1: Linear voltage-dependent propagation loss coefficient
          for the first arm.
        dloss_dv_2: Linear voltage-dependent propagation loss coefficient
          for the second arm.
        dloss_dv2_1: Quadratic voltage-dependent propagation loss
          coefficient for the first arm.
        dloss_dv2_2: Quadratic voltage-dependent propagation loss
          coefficient for the second arm.
        ports: List of port names. If not set, the *sorted* list of port
          names from the component is used.

    Notes:
        For multimode ports, mixed-mode coefficients are 0. Parameters can
        be specified per mode by using sequences of values. Dispersion for
        ``tau1``, ``tau2``, ``kappa1``, and ``kappa2`` can also be manually
        included by setting the coefficients to an :class:`Interpolator`
        (with multiple values for multimode ports), or a 2D array with shape
        (M, N), in which M is the number of modes, and N the length of the
        frequency sequence used in the S matrix computation.
    """

    def __init__(
        self,
        *,
        n_eff1: _ComplexCoeff | Interpolator,
        n_eff2: _ComplexCoeff | Interpolator | None = None,
        length1: pft.Coordinate,
        length2: pft.Coordinate | None = None,
        tau1: _ComplexCoeff | Interpolator | None = None,
        tau2: _ComplexCoeff | Interpolator | None = None,
        kappa1: _ComplexCoeff | Interpolator = -1j * 2**-0.5,
        kappa2: _ComplexCoeff | Interpolator = -1j * 2**-0.5,
        propagation_loss1: pft.PropagationLoss | Sequence[pft.PropagationLoss] = 0.0,
        propagation_loss2: pft.PropagationLoss | Sequence[pft.PropagationLoss] = 0.0,
        extra_loss1: pft.Loss | Sequence[pft.Loss] = 0.0,
        extra_loss2: pft.Loss | Sequence[pft.Loss] = 0.0,
        n_group1: float | Sequence[float] | None = None,
        n_group2: float | Sequence[float] | None = None,
        dispersion1: pft.Dispersion | Sequence[pft.Dispersion] = 0.0,
        dispersion2: pft.Dispersion | Sequence[pft.Dispersion] = 0.0,
        dispersion_slope1: pft.DispersionSlope | Sequence[pft.DispersionSlope] = 0.0,
        dispersion_slope2: pft.DispersionSlope | Sequence[pft.DispersionSlope] = 0.0,
        reference_frequency: pft.Frequency | None = None,
        dn1_dT: pft.annotate(complex | Sequence[complex], label="dn1/dT", units="1/K") = 0.0,
        dn2_dT: pft.annotate(complex | Sequence[complex], label="dn2/dT", units="1/K") = 0.0,
        dL1_dT: pft.annotate(float | Sequence[float], label="dL1/dT", units="dB/μm/K") = 0.0,
        dL2_dT: pft.annotate(float | Sequence[float], label="dL2/dT", units="dB/μm/K") = 0.0,
        temperature1: pft.Temperature = 293.0,
        temperature2: pft.Temperature = 293.0,
        reference_temperature: pft.Temperature = 293.0,
        voltage1: pft.Voltage = 0.0,
        voltage2: pft.Voltage = 0.0,
        v_piL1: pft.annotate(float, label="VπL1", units="V·μm") | None = None,
        v_piL2: pft.annotate(float, label="VπL2", units="V·μm") | None = None,
        dloss_dv_1: pft.annotate(float, label="dL/dV", units="dB/μm/V") = 0,
        dloss_dv_2: pft.annotate(float, label="dL/dV", units="dB/μm/V") = 0,
        dloss_dv2_1: pft.annotate(float, label="d²L/dV²", units="dB/μm/V²") = 0,
        dloss_dv2_2: pft.annotate(float, label="d²L/dV²", units="dB/μm/V²") = 0,
        ports: Sequence[str] | None = None,
    ) -> None:
        super().__init__(
            n_eff1=_ensure_correct_shape(n_eff1),
            n_eff2=n_eff2,
            length1=float(length1),
            length2=length2,
            tau1=tau1,
            tau2=tau2,
            kappa1=_ensure_correct_shape(kappa1),
            kappa2=_ensure_correct_shape(kappa2),
            propagation_loss1=_ensure_correct_shape(propagation_loss1),
            propagation_loss2=_ensure_correct_shape(propagation_loss2),
            extra_loss1=_ensure_correct_shape(extra_loss1),
            extra_loss2=_ensure_correct_shape(extra_loss2),
            n_group1=n_group1,
            n_group2=n_group2,
            dispersion1=_ensure_correct_shape(dispersion1),
            dispersion2=_ensure_correct_shape(dispersion2),
            dispersion_slope1=_ensure_correct_shape(dispersion_slope1),
            dispersion_slope2=_ensure_correct_shape(dispersion_slope2),
            reference_frequency=reference_frequency,
            dn1_dT=_ensure_correct_shape(dn1_dT),
            dn2_dT=_ensure_correct_shape(dn2_dT),
            dL1_dT=_ensure_correct_shape(dL1_dT),
            dL2_dT=_ensure_correct_shape(dL2_dT),
            temperature1=float(temperature1),
            temperature2=float(temperature2),
            reference_temperature=float(reference_temperature),
            voltage1=float(voltage1),
            voltage2=float(voltage2),
            v_piL1=v_piL1,
            v_piL2=v_piL2,
            dloss_dv_1=dloss_dv_1,
            dloss_dv_2=dloss_dv_2,
            dloss_dv2_1=dloss_dv2_1,
            dloss_dv2_2=dloss_dv2_2,
            ports=ports,
        )

    def black_box_component(
        self,
        port_spec: str | PortSpec | None = None,
        technology: Technology | None = None,
        name: str | None = None,
    ) -> Component:
        """Create a black-box component using this model for testing.

        Args:
            port_spec: Port specification used in the component. If ``None``,
              look for ``"port_spec"`` in :attr:`config.default_kwargs`.
            technology: Component technology. If ``None``, the default
              technology is used.
            name: Component name. If ``None`` a default is used.

        Returns:
            Component with ports and model.
        """
        p = self.parametric_kwargs

        model_name = self.__class__.__name__[:-5]
        component = Component(f"BB{model_name}" if name is None else name, technology=technology)
        component.properties.__thumbnail__ = "mzm"

        if port_spec is None:
            port_spec = config.default_kwargs.get("port_spec")
            if port_spec is None:
                raise RuntimeError("Missing argument 'port_spec'.")
        if isinstance(port_spec, str):
            name = port_spec
            port_spec = component.technology.ports.get(port_spec)
            if port_spec is None:
                raise RuntimeError(f"Port spec '{name}' not found in component's technology.")

        width = port_spec.width
        dc_length = width * 8
        length1 = p["length1"]
        if length1 <= 0:
            length1 = dc_length
        length2 = p["length2"] or length1
        if length2 <= 0:
            length2 = dc_length
        if max(length1, length2) > 3 * dc_length:
            length1 *= 3 * dc_length / max(length1, length2)
            length2 *= 3 * dc_length / max(length1, length2)

        p1 = [
            (0, -0.75 * width),
            (0.25 * dc_length, -0.75 * width),
            (0.75 * dc_length, 0.75 * width),
            (dc_length, 0.75 * width),
            (dc_length, 0.75 * width + 0.5 * length2),
            (2 * width + dc_length, 0.75 * width + 0.5 * length2),
            (2 * width + dc_length, 0.75 * width),
            (2 * width + 1.25 * dc_length, 0.75 * width),
            (2 * width + 1.75 * dc_length, -0.75 * width),
            (2 * width + 2 * dc_length, -0.75 * width),
        ]
        p2 = [
            (0, 0.75 * width),
            (0.25 * dc_length, 0.75 * width),
            (0.75 * dc_length, -0.75 * width),
            (dc_length, -0.75 * width),
            (dc_length, -0.75 * width - 0.5 * length1),
            (2 * width + dc_length, -0.75 * width - 0.5 * length1),
            (2 * width + dc_length, -0.75 * width),
            (2 * width + 1.25 * dc_length, -0.75 * width),
            (2 * width + 1.75 * dc_length, 0.75 * width),
            (2 * width + 2 * dc_length, 0.75 * width),
        ]

        profiles = port_spec.path_profiles_list()
        if len(profiles) == 0:
            profiles = [(width, 0, _bb_layer)]

        for w, g, layer in profiles:
            polygons = boolean(
                Path(p1[0], w, g).segment(p1[1:]), Path(p2[0], w, g).segment(p2[1:]), "+"
            )
            component.add(layer, *polygons)

        _add_bb_text(component, width)

        port_names = self.parametric_kwargs["ports"] or [None] * 4
        component.add_port(Port(p1[0], 0, port_spec), port_names[0])
        component.add_port(Port(p2[0], 0, port_spec), port_names[1])
        component.add_port(Port(p2[-1], 180, port_spec), port_names[2])
        component.add_port(Port(p1[-1], 180, port_spec), port_names[3])

        component.add_model(self, model_name)
        return component

    def start(
        self,
        component: Component,
        frequencies: Sequence[pft.Frequency],
        temperature1: pft.Temperature | None = None,
        voltage1: pft.Voltage | None = None,
        temperature2: pft.Temperature | None = None,
        voltage2: pft.Voltage | None = None,
        **kwargs,
    ) -> SMatrix:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            temperature1: Operating temperature override for first arm.
            temperature2: Operating temperature override for second arm.
            voltage1: Operating voltage override for first arm.
            voltage2: Operating voltage override for second arm.
            **kwargs: Unused.

        Returns:
           Result object with attributes ``status`` and ``s_matrix``.
        """
        classification = frequency_classification(frequencies)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if len(component_ports) != 4:
            raise RuntimeError(
                f"AnalyticMZIModel can only be used on components with 4 ports. '{component.name}' "
                f"has {len(component_ports)} {classification} ports.",
            )

        p = self.parametric_kwargs

        names = p["ports"]
        if names is None:
            names = sorted(component_ports)
        elif not all(name in component_ports for name in names):
            raise RuntimeError(
                f"Not all port names defined in AnalyticMZIModel match the {classification} port "
                f"names in component '{component.name}'."
            )

        num_modes = component_ports[names[0]].num_modes
        if not all(port.num_modes == num_modes for port in component_ports.values()):
            raise RuntimeError(
                f"AnalyticMZIModel requires that all ports have the same number of modes. Ports "
                f"from '{component.name}' support different numbers of modes."
            )

        frequencies = numpy.asarray(frequencies)

        if temperature1 is None:
            temperature1 = p["temperature1"]

        if temperature2 is None:
            temperature2 = p["temperature2"]

        if voltage1 is None:
            voltage1 = p["voltage1"]

        if voltage2 is None:
            voltage2 = p["voltage2"]

        n_eff1 = _sample(component.name, "n_eff1", p["n_eff1"], frequencies, num_modes)
        n_eff2 = p["n_eff2"]
        if n_eff2 is None:
            n_eff2 = n_eff1
        else:
            n_eff2 = _sample(
                component.name, "n_eff2", _ensure_correct_shape(n_eff2), frequencies, num_modes
            )

        t1 = _ensure_correct_shape(
            _waveguide_transmission(
                frequencies,
                p["length1"],
                n_eff1,
                p["n_group1"],
                p["dispersion1"],
                p["dispersion_slope1"],
                p["reference_frequency"],
                p["propagation_loss1"],
                p["extra_loss1"],
                p["dn1_dT"],
                p["dL1_dT"],
                temperature1,
                p["reference_temperature"],
                voltage1,
                p["v_piL1"],
                p["dloss_dv_1"],
                p["dloss_dv2_1"],
            )
        )

        t2 = _ensure_correct_shape(
            _waveguide_transmission(
                frequencies,
                p["length2"] or p["length1"],
                n_eff2,
                p["n_group2"],
                p["dispersion2"],
                p["dispersion_slope2"],
                p["reference_frequency"],
                p["propagation_loss2"],
                p["extra_loss2"],
                p["dn2_dT"],
                p["dL2_dT"],
                temperature2,
                p["reference_temperature"],
                voltage2,
                p["v_piL2"],
                p["dloss_dv_2"],
                p["dloss_dv2_2"],
            )
        )

        kappa1 = _sample(component.name, "kappa1", p["kappa1"], frequencies, num_modes)
        kappa2 = _sample(component.name, "kappa2", p["kappa2"], frequencies, num_modes)

        tau1 = p["tau1"]
        if tau1 is None:
            tau1 = 1j * numpy.exp(1j * numpy.angle(kappa1)) * numpy.sqrt(1 - numpy.abs(kappa1) ** 2)
        else:
            tau1 = _sample(
                component.name, "tau1", _ensure_correct_shape(tau1), frequencies, num_modes
            )

        tau2 = p["tau2"]
        if tau2 is None:
            tau2 = 1j * numpy.exp(1j * numpy.angle(kappa2)) * numpy.sqrt(1 - numpy.abs(kappa2) ** 2)
        else:
            tau2 = _sample(
                component.name, "tau2", _ensure_correct_shape(tau2), frequencies, num_modes
            )

        s20 = tau1 * t1 * tau2 + kappa1 * t2 * kappa2
        s30 = tau1 * t1 * kappa2 + kappa1 * t2 * tau2
        s21 = kappa1 * t1 * tau2 + tau1 * t2 * kappa2
        s31 = kappa1 * t1 * kappa2 + tau1 * t2 * tau2

        s = (
            (None, None, s20, s30),
            (None, None, s21, s31),
            (s20, s21, None, None),
            (s30, s31, None, None),
        )
        elements = {
            (f"{port_in}@{mode}", f"{port_out}@{mode}"): s[j][i][mode]
            for i, port_in in enumerate(names)
            for j, port_out in enumerate(names)
            for mode in range(component_ports[port_in].num_modes)
            if s[j][i] is not None
        }
        return SMatrix(frequencies, elements, component_ports)


register_model_class(TerminationModel)
register_model_class(TwoPortModel)
register_model_class(PowerSplitterModel)
register_model_class(PolarizationBeamSplitterModel)
register_model_class(PolarizationSplitterRotatorModel)
register_model_class(DirectionalCouplerModel)
register_model_class(CrossingModel)
register_model_class(WaveguideModel)
register_model_class(AnalyticWaveguideModel)
register_model_class(AnalyticDirectionalCouplerModel)
register_model_class(AnalyticMZIModel)
