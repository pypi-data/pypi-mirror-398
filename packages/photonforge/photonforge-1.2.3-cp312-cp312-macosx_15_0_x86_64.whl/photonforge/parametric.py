# No pollution of the parametric namespace
import itertools as _it
import typing as _typ
import warnings as _warn
from collections.abc import Sequence as _Sequence

import numpy as _np

import photonforge as _pf

from . import extension as _ext
from . import typing as _pft
from .analytic_models import WaveguideModel as _WaveguideModel
from .circuit_model import CircuitModel as _CircuitModel
from .tidy3d_model import Tidy3DModel as _Tidy3DModel

_OptDimension = _pft.annotate(_pft.Dimension, optional=True)
_OptPositiveDimension = _pft.annotate(_pft.PositiveDimension, optional=True)
_OptDimension2D = _pft.annotate(_pft.Dimension2D, optional=True)
_OptCoord = _pft.annotate(_pft.Coordinate, optional=True)
_OptCoords = _pft.annotate(_Sequence[_pft.Coordinate2D], optional=True)
_OptOffsets = _pft.annotate(
    _pft.Coordinate | _pft.annotate(_Sequence[_pft.Coordinate], minItems=2, maxItems=2),
    optional=True,
)
_OptAngle = _pft.annotate(_pft.Angle, minimum=-180, maximum=180, optional=True)

_OptFraction = _pft.annotate(_pft.Fraction, optional=True)
_OptFractions = _pft.annotate(
    _pft.Fraction | _pft.annotate(_typ.Sequence[_pft.Fraction], minItems=2, maxItems=2),
    optional=True,
)

_OptIntTurns = _pft.annotate(int, minimum=2, optional=True)

_OptJoin = _pft.annotate(_typ.Literal["round"] | float, optional=True)

_OptBool = _pft.annotate(bool, optional=True)

_OptAxis = _pft.annotate(_typ.Literal["", "x", "y"], optional=True)

_OptLayer = _pft.annotate(_pft.Layer, optional=True)

_OptVariableFraction = _pft.annotate(_pft.expression(1, 1), optional=True)

_OptVariableOffset = _pft.annotate(float | _pft.expression(1, 1), units="μm", optional=True)

_PortSpec_x2 = _pft.annotate(_Sequence[_pft.PortSpecOrName], minItems=2, maxItems=2)
_PortSpecPair = _pft.PortSpecOrName | _PortSpec_x2

_Port = _ext.Port | _pft.PortReference
_Terminal = _ext.Terminal | _pft.TerminalReference

_OptComponent = _pft.annotate(_pf.Component, optional=True)
_OptModel = _pft.annotate(_pf.Model, optional=True)
_OptTechnology = _pft.annotate(_pf.Technology, optional=True)
_OptStr = _pft.annotate(str, optional=True)


def _get_default(function, kwarg, value, default=None):
    if value is not None:
        return value

    func_kwargs = _pf.config.default_kwargs.get(function)
    if isinstance(func_kwargs, dict):
        value = func_kwargs.get(kwarg)
        if value is not None:
            return value

    value = _pf.config.default_kwargs.get(kwarg)
    if value is not None:
        return value

    if default is not None:
        return default

    raise TypeError(f"{function}() missing 1 required keyword-only argument: '{kwarg}'")


@_pf.parametric_component
def straight(
    *,
    port_spec: _pft.PortSpecOrName | None = None,
    length: _pft.PositiveDimension | None = None,
    bulge_width: _OptCoord | None = None,
    bulge_taper_length: _OptDimension | None = None,
    bulge_margin: _OptDimension | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    active_model: _pft.annotate(_typ.Literal["Tidy3D", "Waveguide"], optional=True, deprecated=True)
    | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
    waveguide_model_kwargs: _pft.kwargs_for(_WaveguideModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Straight waveguide section.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        length: Section length.
        bulge_width: Width added to the waveguide cross-section in the
          central region when ``length`` if enough to fit in 2 tapering
          sections plus margins. If ``None``, defaults to 0.
        bulge_taper_length: Length of each tapering region for bulging the
          central region of the waveguide. If ``None``, defaults to 0.
        bulge_margin: Length of the waveguide that must be kept without
          bulging at both ends. If ``None``, defaults to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.WaveguideModel` is used.
        active_model: *(DEPRECATED)* Name of the model to be used by
          default; must be either ``"Tidy3D"`` or ``"Waveguide"``.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.
        waveguide_model_kwargs: *(DEPRECATED)* Dictionary of keyword
          arguments passed to the component's
          :class:`photonforge.WaveguideModel`.

    Returns:
        Component with the straight section, ports and model.
    """
    function = "straight"
    port_spec = _get_default(function, "port_spec", port_spec)
    length = _get_default(function, "length", length)
    bulge_width = _get_default(function, "bulge_width", bulge_width, 0)
    bulge_taper_length = _get_default(function, "bulge_taper_length", bulge_taper_length, 0)
    bulge_margin = _get_default(function, "bulge_margin", bulge_margin, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _WaveguideModel())

    if (
        active_model is not None
        or tidy3d_model_kwargs is not None
        or waveguide_model_kwargs is not None
    ):
        _warn.warn(
            "Arguments 'active_model', 'tidy3d_model_kwargs', and 'waveguide_model_kwargs' are "
            "deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        active_model = _get_default(function, "active_model", active_model, "Waveguide")
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        waveguide_model_kwargs = _get_default(
            function, "waveguide_model_kwargs", waveguide_model_kwargs, {}
        )
        if active_model == "Waveguide":
            model = _WaveguideModel(**waveguide_model_kwargs)
        else:
            model_kwargs = {"port_symmetries": [(1, 0)]}
            model_kwargs.update(tidy3d_model_kwargs)
            model = _Tidy3DModel(**model_kwargs)

    if technology is None:
        technology = _pf.config.default_technology
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "wg"
    c.add_model(model)

    bulge_region = (bulge_margin + bulge_taper_length, length - bulge_margin - bulge_taper_length)
    if (
        bulge_width != 0
        and bulge_taper_length > 0
        and bulge_margin >= 0
        and bulge_region[1] >= bulge_region[0]
    ):
        for width, offset, layer in port_spec.path_profiles_list():
            path = _pf.Path((0, 0), width, offset)
            if bulge_margin > 0:
                path.segment((bulge_margin, 0))
            path.segment((bulge_region[0], 0), width + bulge_width)
            if bulge_region[1] > bulge_region[0]:
                path.segment((bulge_region[1], 0))
            path.segment((length - bulge_margin, 0), width)
            if bulge_margin > 0:
                path.segment((length, 0))
            c.add(layer, path)
    else:
        for layer, path in port_spec.get_paths((0, 0)):
            c.add(layer, path.segment((length, 0)))

    c.add_port(_pf.Port((0, 0), 0, port_spec))
    c.add_port(_pf.Port((length, 0), 180, port_spec, inverted=True))

    return c


@_pf.parametric_component
def transition(
    *,
    port_spec1: _pft.annotate(_pft.PortSpecOrName, label="Port Spec 1") | None = None,
    port_spec2: _pft.annotate(_pft.PortSpecOrName, label="Port Spec 2") | None = None,
    length: _pft.PositiveDimension | None = None,
    constant_length: _OptDimension | None = None,
    profile: _OptVariableFraction | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Straight waveguide that works as a transition between port profiles.

    Args:
        port_spec1: Port specification describing the first cross-section.
        port_spec2: Port specification describing the second cross-section.
        length: Transition length.
        constant_length: Constant cross-section length added to both ends.
          If ``None``, defaults to 0.
        profile: String expression describing the transition shape
          parametrized by the independent variable ``"u"``, ranging from 0
          to 1 along the transition. The expression must evaluate to a float
          between 0 and 1 representing the weight of the second profile with
          respect to the first at that position. Alternatively, an
          :class:`photonforge.Expression` with 1 parameter can be used. If
          ``None``, a linear transition is used.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Component with the transition geometry, ports and model.
    """
    function = "transition"
    port_spec1 = _get_default(function, "port_spec1", port_spec1)
    port_spec2 = _get_default(function, "port_spec2", port_spec2)
    length = _get_default(function, "length", length)
    constant_length = _get_default(function, "constant_length", constant_length, 0)
    profile = _get_default(function, "profile", profile, "u")
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    if length <= 0 and constant_length <= 0:
        raise ValueError("Transition length cannot be 0.")

    if isinstance(profile, _pf.Expression):
        parameter = profile.parameters
        if len(parameter) != 1:
            raise TypeError("Profile expression must contain 1 parameter only.")
        expressions = profile.expressions
        if len(expressions) == 0:
            raise TypeError("Profile expression must contain at least 1 expression.")
    elif isinstance(profile, str):
        parameter = ["u"]
        expressions = [("p", profile)]

    value_name = expressions[-1][0]

    def interp(a, b):
        return _pf.Expression(
            parameter,
            [*expressions, f"{a} + {value_name} * {b - a}", f"{b - a}"],
        )

    if technology is None:
        technology = _pf.config.default_technology
    if isinstance(port_spec1, str):
        port_spec1 = technology.ports[port_spec1]
    if isinstance(port_spec2, str):
        port_spec2 = technology.ports[port_spec2]

    path_profiles1 = port_spec1.path_profiles_list()
    path_profiles2 = port_spec2.path_profiles_list()

    only1 = {layer for _, _, layer in path_profiles1}
    only2 = {layer for _, _, layer in path_profiles2}
    both = only1.intersection(only2)
    only1 -= both
    only2 -= both

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "transition"
    c.add_model(model)

    start_point = (constant_length, 0)
    mid_point = (constant_length + length, 0)
    end_point = (2 * constant_length + length, 0)

    for layer in only1:
        for w1, g1, l1 in path_profiles1:
            if l1 != layer:
                continue
            path = _pf.Path((0, 0), w1, g1)
            if constant_length > 0:
                path.segment(start_point, (w1, "constant"), (g1, "constant"))
            if length > 0:
                path.segment(mid_point, width=interp(w1, 0))
            c.add(layer, path)

    for layer in only2:
        for w2, g2, l2 in path_profiles2:
            if l2 != layer:
                continue
            path = _pf.Path(start_point, 0, g2)
            if length > 0:
                path.segment(mid_point, width=interp(0, w2))
            if constant_length > 0:
                path.segment(end_point, (w2, "constant"), (g2, "constant"))
            c.add(layer, path)

    for layer in both:
        prof1 = sorted((g, w) for w, g, l1 in path_profiles1 if l1 == layer)
        prof2 = sorted((g, w) for w, g, l2 in path_profiles2 if l2 == layer)
        combinations = (
            zip(prof1, prof2, strict=False)
            if len(prof1) == len(prof2)
            else _it.product(prof1, prof2)
        )
        for (g1, w1), (g2, w2) in combinations:
            path = _pf.Path((0, 0), w1, g1)
            if constant_length > 0:
                path.segment(start_point, (w1, "constant"), (g1, "constant"))
            if length > 0:
                path.segment(mid_point, width=interp(w1, w2), offset=interp(g1, g2))
            else:
                c.add(layer, path)
                path = _pf.Path(mid_point, w2, g2)
            if constant_length > 0:
                path.segment(end_point, (w2, "constant"), (g2, "constant"))
            c.add(layer, path)

    c.add_port(_pf.Port((0, 0), 0, port_spec1))
    c.add_port(_pf.Port(end_point, 180, port_spec2, inverted=True))

    return c


@_pf.parametric_component
def bend(
    *,
    port_spec: _pft.PortSpecOrName | None = None,
    radius: _pft.PositiveDimension | None = None,
    angle: _OptAngle | None = None,
    euler_fraction: _OptFraction | None = None,
    port_bends: _OptBool | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    active_model: _pft.annotate(_typ.Literal["Tidy3D", "Waveguide"], optional=True, deprecated=True)
    | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
    waveguide_model_kwargs: _pft.kwargs_for(_WaveguideModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Waveguide bend section.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        radius: Central arc radius.
        angle: Arc coverage angle. If ``None``, defaults to 90.
        euler_fraction: Fraction of the bend that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        port_bends: Flag controllig whether to set a bend radius for the
          ports. Not used when ``euler_factor > 0``. If ``None``, defaults
          to ``False``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.WaveguideModel` is used.
        active_model: *(DEPRECATED)* Name of the model to be used by
          default; must be either ``"Tidy3D"`` or ``"Waveguide"``.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.
        waveguide_model_kwargs: *(DEPRECATED)* Dictionary of keyword
          arguments passed to the component's
          :class:`photonforge.WaveguideModel`.

    Returns:
        Component with the circular bend section, ports and model.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "bend"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    radius = _get_default(
        function,
        "radius",
        radius,
        port_spec.default_radius if port_spec.default_radius > 0 else None,
    )

    angle = _get_default(function, "angle", angle, 90)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    port_bends = _get_default(function, "port_bends", port_bends, False)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _WaveguideModel())

    if (
        active_model is not None
        or tidy3d_model_kwargs is not None
        or waveguide_model_kwargs is not None
    ):
        _warn.warn(
            "Arguments 'active_model', 'tidy3d_model_kwargs', and 'waveguide_model_kwargs' are "
            "deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        active_model = _get_default(function, "active_model", active_model, "Waveguide")
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        waveguide_model_kwargs = _get_default(
            function, "waveguide_model_kwargs", waveguide_model_kwargs, {}
        )
        if active_model == "Waveguide":
            model = _WaveguideModel(**waveguide_model_kwargs)
        else:
            model_kwargs = {"port_symmetries": [(1, 0)]}
            model_kwargs.update(tidy3d_model_kwargs)
            model = _Tidy3DModel(**model_kwargs)

    if angle % 90 != 0:
        _warn.warn(
            "Using bends with angles not multiples of 90° might lead to disconnected waveguides. "
            "Consider building a continuous path with grid-aligned ports instead of connecting "
            "sections with non grid-aligned ports.",
            RuntimeWarning,
            3,
        )

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "bend"
    c.add_model(model)

    p0 = c.add_port(_pf.Port((0, 0), 0, port_spec))
    path_length = None
    if angle > 0:
        radians = (angle - 90) / 180.0 * _np.pi
        endpoint = (radius * _np.cos(radians), radius * (1 + _np.sin(radians)))
        for layer, path in port_spec.get_paths((0, 0)):
            path.arc(-90, angle - 90, radius, euler_fraction=euler_fraction, endpoint=endpoint)
            c.add(layer, path)
            if path_length is None:
                path_length = path.length()
        p1 = c.add_port(_pf.Port(endpoint, angle - 180, port_spec, inverted=True))
        if port_bends and euler_fraction == 0:
            c[p0].bend_radius = radius
            c[p1].bend_radius = -radius
    else:
        radians = (90 + angle) / 180.0 * _np.pi
        endpoint = (radius * _np.cos(radians), radius * (-1 + _np.sin(radians)))
        for layer, path in port_spec.get_paths((0, 0)):
            path.arc(90, 90 + angle, radius, euler_fraction=euler_fraction, endpoint=endpoint)
            c.add(layer, path)
            if path_length is None:
                path_length = path.length()
        p1 = c.add_port(_pf.Port(endpoint, angle + 180, port_spec, inverted=True))
        if port_bends and euler_fraction == 0:
            c[p0].bend_radius = -radius
            c[p1].bend_radius = radius

    return c


@_pf.parametric_component
def s_bend(
    *,
    port_spec: _pft.PortSpecOrName | None = None,
    length: _OptPositiveDimension | None = None,
    offset: _pft.Coordinate | None = None,
    euler_fraction: _OptFraction | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    active_model: _pft.annotate(_typ.Literal["Tidy3D", "Waveguide"], optional=True, deprecated=True)
    | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
    waveguide_model_kwargs: _pft.kwargs_for(_WaveguideModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """S bend waveguide section.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        length: Length of the S bend in the main propagation direction. If
          ``None``, a default is calculated based on the default bend
          radius, if possible.
        offset: Side offset of the S bend.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.WaveguideModel` is used.
        active_model: *(DEPRECATED)* Name of the model to be used by
          default; must be either ``"Tidy3D"`` or ``"Waveguide"``.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.
        waveguide_model_kwargs: *(DEPRECATED)* Dictionary of keyword
          arguments passed to the component's
          :class:`photonforge.WaveguideModel`.

    Returns:
        Component with the S bend section, ports and model.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "s_bend"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    offset = _get_default(function, "offset", offset)
    default_length = None
    if length is None:
        abs_offset = abs(offset)
        radius = _get_default("bend", "radius", None, port_spec.default_radius)
        if 4 * radius > abs_offset:
            default_length = _pf.s_bend_length(abs_offset, radius)
    length = _get_default(function, "length", length, default_length)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _WaveguideModel())

    if (
        active_model is not None
        or tidy3d_model_kwargs is not None
        or waveguide_model_kwargs is not None
    ):
        _warn.warn(
            "Arguments 'active_model', 'tidy3d_model_kwargs', and 'waveguide_model_kwargs' are "
            "deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        active_model = _get_default(function, "active_model", active_model, "Waveguide")
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        waveguide_model_kwargs = _get_default(
            function, "waveguide_model_kwargs", waveguide_model_kwargs, {}
        )
        if active_model == "Waveguide":
            model = _WaveguideModel(**waveguide_model_kwargs)
        else:
            model_kwargs = {"port_symmetries": [(1, 0)]}
            model_kwargs.update(tidy3d_model_kwargs)
            model = _Tidy3DModel(**model_kwargs)

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "s-bend"
    c.add_model(model)

    path_length = None
    for layer, path in port_spec.get_paths((0, 0)):
        c.add(layer, path.s_bend((length, offset), euler_fraction))
        if path_length is None:
            path_length = path.length()

    c.add_port(_pf.Port((0, 0), 0, port_spec))
    c.add_port(_pf.Port((length, offset), 180, port_spec, inverted=True))

    return c


@_pf.parametric_component
def crossing(
    *,
    port_spec: _PortSpecPair | None = None,
    arm_length: _pft.PositiveDimension | None = None,
    added_width: _OptVariableOffset | None = None,
    extra_length: _OptDimension | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Waveguide crossing.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each waveguide.
        arm_length: Length of a single crossing arm.
        added_width: Width added to the arm linearly up to the center. An
          expression or string (with independent variable ``"u"``) can also
          be used. If ``None``, defaults to 0.
        extra_length: Additional length for a straight section at the ports.
          If ``None``, defaults to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Component with the crossing, ports and model.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "crossing"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    arm_length = _get_default(function, "arm_length", arm_length)
    added_width = _get_default(function, "added_width", added_width, 0)
    extra_length = _get_default(function, "extra_length", extra_length, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    if isinstance(added_width, _pf.Expression):
        p = added_width.parameters
        if len(p) != 1:
            raise TypeError("Profile expression must contain 1 parameter only.")
        p = p[0]
        expressions = added_width.expressions
        if len(expressions) == 0:
            raise TypeError("Profile expression must contain at least 1 expression.")
    elif isinstance(added_width, str):
        p = "u"
        expressions = [("p", added_width)]
    else:
        p = "u"
        expressions = [("p", f"{added_width}*u")]

    value_name = expressions[-1][0]
    names = [p] + [k for k, v in expressions]
    i = 0
    while f"{p}_{i}" in names:
        i += 1
    parameter = f"{p}_{i}"
    expressions.insert(0, (p, f"1 - abs(1 - 2 * {parameter})"))

    length = arm_length + extra_length

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "crossing"
    c.add_model(model)

    for i in range(2):
        v = 1 - i + 1j * i
        for width, offset, layer in port_spec[i].path_profiles_list():
            width_expr = _pf.Expression(
                parameter, [*expressions, f"{width} + {value_name}", ("derivative", 0)]
            )
            arm = _pf.Path(-length * v, width, offset)
            if length > arm_length:
                arm.segment(-arm_length * v)
            arm.segment(arm_length * v, width=width_expr)
            if length > arm_length:
                arm.segment(length * v)
            c.add(layer, arm)

    c.add_port(_pf.Port((-length, 0), 0, port_spec[0]))
    c.add_port(_pf.Port((0, -length), 90, port_spec[1]))
    c.add_port(_pf.Port((length, 0), 180, port_spec[0], inverted=True))
    c.add_port(_pf.Port((0, length), -90, port_spec[1], inverted=True))

    return c


@_pf.parametric_component
def crossing45(
    *,
    port_spec: _PortSpecPair | None = None,
    arm_length: _pft.PositiveDimension | None = None,
    added_width: _OptVariableOffset | None = None,
    extra_length: _OptDimension | None = None,
    radius: _pft.PositiveDimension | None = None,
    euler_fraction: _OptFraction | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """45° waveguide crossing.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each waveguide.
        arm_length: Length of a single crossing arm.
        added_width: Width added to the arm linearly up to the center. An
          expression or string (with independent variable ``"u"``) can also
          be used. If ``None``, defaults to 0.
        extra_length: Additional length for a straight section at the ports.
          If ``None``, defaults to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        radius: Radius used for arm bends.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Component with the crossing, ports and model.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "crossing45"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    radius = [
        _get_default(
            function,
            "radius",
            radius,
            port_spec[i].default_radius if port_spec[i].default_radius > 0 else None,
        )
        for i in range(2)
    ]

    arm_length = _get_default(function, "arm_length", arm_length)
    added_width = _get_default(function, "added_width", added_width, 0)
    extra_length = _get_default(function, "extra_length", extra_length, 0)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    if isinstance(added_width, _pf.Expression):
        p = added_width.parameters
        if len(p) != 1:
            raise TypeError("Profile expression must contain 1 parameter only.")
        p = p[0]
        expressions = added_width.expressions
        if len(expressions) == 0:
            raise TypeError("Profile expression must contain at least 1 expression.")
    elif isinstance(added_width, str):
        p = "u"
        expressions = [("p", added_width)]
    else:
        p = "u"
        expressions = [("p", f"{added_width}*u")]

    value_name = expressions[-1][0]
    names = [p] + [k for k, v in expressions]
    i = 0
    while f"{p}_{i}" in names:
        i += 1
    parameter = f"{p}_{i}"
    expressions.insert(0, (p, f"1 - abs(1 - 2 * {parameter})"))

    projected_arm_length = arm_length * 2**-0.5
    projected_extra_length = extra_length * 2**-0.5
    projected_length = projected_arm_length + projected_extra_length

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "crossing"
    c.add_model(model)

    xp = [None, None]
    yp = [None, None]
    for i in range(2):
        sign = 1 - 2 * i
        arc_x = radius[i] * 2**-0.5
        arc_y = radius[i] - arc_x
        old_grid = _pf.config.grid
        _pf.config.grid = _pf.config.tolerance
        xp[i] = _pf.snap_to_grid(projected_arm_length + projected_extra_length + arc_x)
        yp[i] = _pf.snap_to_grid(projected_arm_length + projected_extra_length + arc_y)
        _pf.config.grid = old_grid

        for width, offset, layer in port_spec[i].path_profiles_list():
            width_expr = _pf.Expression(
                parameter, [*expressions, f"{width} + {value_name}", ("derivative", 0)]
            )
            arm = _pf.Path((-xp[i], -sign * yp[i]), width, offset)
            arm.arc(
                -sign * 90,
                -sign * 45,
                radius[i],
                euler_fraction=euler_fraction,
                endpoint=(-projected_length, -sign * projected_length),
            )
            if projected_length > projected_arm_length:
                arm.segment((-projected_arm_length, -sign * projected_arm_length))
            arm.segment((projected_arm_length, sign * projected_arm_length), width=width_expr)
            if projected_length > projected_arm_length:
                arm.segment((projected_length, sign * projected_length))
            arm.arc(
                sign * 135,
                sign * 90,
                radius[i],
                euler_fraction=euler_fraction,
                endpoint=(xp[i], sign * yp[i]),
            )
            c.add(layer, arm)

    c.add_port(_pf.Port((-xp[0], -yp[0]), 0, port_spec[0]))
    c.add_port(_pf.Port((-xp[1], yp[1]), 0, port_spec[1]))
    c.add_port(_pf.Port((xp[1], -yp[1]), 180, port_spec[1], inverted=True))
    c.add_port(_pf.Port((xp[0], yp[0]), 180, port_spec[0], inverted=True))

    return c


@_pf.parametric_component
def ring_coupler(
    *,
    port_spec: _PortSpecPair | None = None,
    coupling_distance: _pft.Coordinate | None = None,
    radius: _pft.PositiveDimension | None = None,
    bus_length: _OptDimension | None = None,
    euler_fraction: _OptFraction | None = None,
    coupling_length: _OptDimension | None = None,
    port_bends: _OptBool | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Ring/straight coupling region.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each coupler side.
        coupling_distance: Distance between bus and ring waveguide centers.
        radius: Central ring radius.
        bus_length: Length of the bus waveguide added to each side of the
          straight coupling section. If both ``bus_length`` and
          ``coupling_length`` are 0, the bus waveguide is not included. If
          ``None``, defaults to radius.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        coupling_length: Length of straight coupling region. If ``None``,
          defaults to 0.
        port_bends: Flag controllig whether to set a bend radius for the
          ports. Not used when ``euler_factor > 0``. If ``None``, defaults
          to ``False``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Coupling component.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "ring_coupler"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    coupling_distance = _get_default(function, "coupling_distance", coupling_distance)

    radius = _get_default(
        function,
        "radius",
        radius,
        port_spec[1].default_radius if port_spec[1].default_radius > 0 else None,
    )

    bus_length = _get_default(function, "bus_length", bus_length, radius)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    coupling_length = _get_default(function, "coupling_length", coupling_length, 0)
    port_bends = _get_default(function, "port_bends", port_bends, False)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "dc"
    c.add_model(model)

    xp = bus_length + 0.5 * coupling_length
    yp = -radius - coupling_distance
    xr = radius + 0.5 * coupling_length
    if xp > 0:
        for layer, path in port_spec[0].get_paths((-xp, yp)):
            c.add(layer, path.segment((xp, yp)))
    for layer, path in port_spec[1].get_paths((xr, 0)):
        path.arc(0, -90, radius, euler_fraction=euler_fraction)
        if coupling_length > 0:
            path.segment((-0.5 * coupling_length, -radius))
        path.arc(-90, -180, radius, endpoint=(-xr, 0), euler_fraction=euler_fraction)
        c.add(layer, path)

    if xp > 0:
        c.add_port(_pf.Port((-xp, yp), 0, port_spec[0]))
    p0 = c.add_port(_pf.Port((-xr, 0), -90, port_spec[1], inverted=True))
    if xp > 0:
        c.add_port(_pf.Port((xp, yp), 180, port_spec[0], inverted=True))
    p1 = c.add_port(_pf.Port((xr, 0), -90, port_spec[1]))

    if port_bends and euler_fraction == 0:
        c[p0].bend_radius = radius
        c[p1].bend_radius = -radius

    return c


@_pf.parametric_component
def s_bend_ring_coupler(
    *,
    port_spec: _PortSpecPair | None = None,
    coupling_distance: _pft.Coordinate | None = None,
    radius: _pft.PositiveDimension | None = None,
    s_bend_length: _OptPositiveDimension | None = None,
    s_bend_offset: _pft.Coordinate | None = None,
    euler_fraction: _OptFraction | None = None,
    coupling_length: _OptDimension | None = None,
    port_bends: _OptBool | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Ring coupling through an S bend curve.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each coupler side.
        coupling_distance: Distance between bus and ring waveguide centers.
        radius: Central ring radius.
        s_bend_length: Length of the S bends. If ``None``, a default is
          calculated based on the default bend radius, if possible.
        s_bend_offset: Offset of the S bends.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        coupling_length: Length of straight coupling region. If ``None``,
          defaults to 0.
        port_bends: Flag controllig whether to set a bend radius for the
          ports. Not used when ``euler_factor > 0``. If ``None``, defaults
          to ``False``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Coupling component.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "s_bend_ring_coupler"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    coupling_distance = _get_default(function, "coupling_distance", coupling_distance)

    radius = _get_default(
        function,
        "radius",
        radius,
        port_spec[1].default_radius if port_spec[1].default_radius > 0 else None,
    )

    s_bend_offset = _get_default(function, "s_bend_offset", s_bend_offset)
    default_length = None
    if s_bend_length is None:
        abs_offset = abs(s_bend_offset)
        s_radius = _get_default("bend", "radius", None, port_spec[0].default_radius)
        if 4 * s_radius > abs_offset:
            default_length = _pf.s_bend_length(abs_offset, s_radius)
    s_bend_length = _get_default(function, "s_bend_length", s_bend_length, default_length)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    coupling_length = _get_default(function, "coupling_length", coupling_length, 0)
    port_bends = _get_default(function, "port_bends", port_bends, False)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "dc"
    c.add_model(model)

    xs = s_bend_length + 0.5 * coupling_length
    ys = -radius - coupling_distance - s_bend_offset
    y_mid = -radius - coupling_distance
    for layer, path in port_spec[0].get_paths((-xs, ys)):
        path.s_bend((-0.5 * coupling_length, y_mid), euler_fraction)
        if coupling_length > 0:
            path.segment((0.5 * coupling_length, y_mid))
        path.s_bend((xs, ys), euler_fraction)
        c.add(layer, path)

    xr = radius + 0.5 * coupling_length
    for layer, path in port_spec[1].get_paths((xr, 0)):
        path.arc(0, -90, radius, euler_fraction=euler_fraction)
        if coupling_length > 0:
            path.segment((-0.5 * coupling_length, -radius))
        path.arc(-90, -180, radius, endpoint=(-xr, 0), euler_fraction=euler_fraction)
        c.add(layer, path)

    c.add_port(_pf.Port((-xs, ys), 0, port_spec[0]))
    p0 = c.add_port(_pf.Port((-xr, 0), -90, port_spec[1], inverted=True))
    c.add_port(_pf.Port((xs, ys), 180, port_spec[0], inverted=True))
    p1 = c.add_port(_pf.Port((xr, 0), -90, port_spec[1]))

    if port_bends and euler_fraction == 0:
        c[p0].bend_radius = radius
        c[p1].bend_radius = -radius

    return c


@_pf.parametric_component
def dual_ring_coupler(
    *,
    port_spec: _PortSpecPair | None = None,
    coupling_distance: _pft.Coordinate | None = None,
    radius: _pft.PositiveDimension | None = None,
    euler_fraction: _OptFraction | None = None,
    coupling_length: _OptDimension | None = None,
    port_bends: _OptBool | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Dual ring coupling region.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each coupler side.
        coupling_distance: Distance between bus and ring waveguide centers.
        radius: Central ring radius. A tuple with 2 values can be used, one
          for each coupler side.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        coupling_length: Length of straight coupling region. If ``None``,
          defaults to 0.
        port_bends: Flag controlling whether to set a bend radius for the
          ports. Not used when ``euler_factor > 0``. If ``None``, defaults
          to ``False``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Coupling component.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "dual_ring_coupler"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    coupling_distance = _get_default(function, "coupling_distance", coupling_distance)

    if radius is None or hasattr(radius, "__float__"):
        radius = [radius, radius]
    radius = [
        _get_default(
            function,
            "radius",
            radius[i],
            port_spec[i].default_radius if port_spec[i].default_radius > 0 else None,
        )
        for i in range(2)
    ]

    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    coupling_length = _get_default(function, "coupling_length", coupling_length, 0)
    port_bends = _get_default(function, "port_bends", port_bends, False)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "dc"
    c.add_model(model)

    xr0 = radius[0] + 0.5 * coupling_length
    yr = radius[0] + radius[1] + coupling_distance
    for layer, path in port_spec[0].get_paths((-xr0, -yr)):
        path.arc(180, 90, radius[0], euler_fraction=euler_fraction)
        if coupling_length > 0:
            path.segment((0.5 * coupling_length, -radius[1] - coupling_distance))
        path.arc(90, 0, radius[0], endpoint=(xr0, -yr), euler_fraction=euler_fraction)
        c.add(layer, path)

    xr1 = radius[1] + 0.5 * coupling_length
    for layer, path in port_spec[1].get_paths((xr1, 0)):
        path.arc(0, -90, radius[1], euler_fraction=euler_fraction)
        if coupling_length > 0:
            path.segment((-0.5 * coupling_length, -radius[0]))
        path.arc(-90, -180, radius[1], endpoint=(-xr1, 0), euler_fraction=euler_fraction)
        c.add(layer, path)

    p0 = c.add_port(_pf.Port((-xr0, -yr), 90, port_spec[0]))
    p1 = c.add_port(_pf.Port((-xr1, 0), -90, port_spec[1], inverted=True))
    p2 = c.add_port(_pf.Port((xr0, -yr), 90, port_spec[0], inverted=True))
    p3 = c.add_port(_pf.Port((xr1, 0), -90, port_spec[1]))

    if port_bends and euler_fraction == 0:
        c[p0].bend_radius = -radius[0]
        c[p1].bend_radius = radius[1]
        c[p2].bend_radius = radius[0]
        c[p3].bend_radius = -radius[1]

    return c


@_pf.parametric_component
def s_bend_coupler(
    *,
    port_spec: _PortSpecPair | None = None,
    coupling_distance: _pft.Coordinate | None = None,
    s_bend_length: _OptPositiveDimension | None = None,
    s_bend_offset: _pft.Coordinate | None = None,
    euler_fraction: _OptFraction | None = None,
    coupling_length: _OptDimension | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """S bend coupling region.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each coupler side.
        coupling_distance: Distance between waveguide centers.
        s_bend_length: Length of the S bends. A tuple with 2 values can be
          used, one for each coupler side.
        s_bend_offset: Offset of the S bends. A tuple with 2 values can be
          used, one for each coupler side.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        coupling_length: Length of straight coupling region. If ``None``,
          defaults to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Coupling component.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "s_bend_coupler"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    coupling_distance = _get_default(function, "coupling_distance", coupling_distance)

    if s_bend_offset is None or hasattr(s_bend_offset, "__float__"):
        s_bend_offset = [s_bend_offset, s_bend_offset]
    s_bend_offset = [_get_default(function, "s_bend_offset", s_bend_offset[i]) for i in range(2)]

    if s_bend_length is None or hasattr(s_bend_length, "__float__"):
        s_bend_length = [s_bend_length, s_bend_length]
    for i in range(2):
        default_length = None
        if s_bend_length[i] is None:
            abs_offset = abs(s_bend_offset[i])
            radius = _get_default("bend", "radius", None, port_spec[i].default_radius)
            if 4 * radius > abs_offset:
                default_length = _pf.s_bend_length(abs_offset, radius)
        s_bend_length[i] = _get_default(function, "s_bend_length", s_bend_length[i], default_length)

    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    coupling_length = _get_default(function, "coupling_length", coupling_length, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "dc"
    c.add_model(model)

    x_out0 = 2 * s_bend_length[0] + coupling_length
    x_out1 = s_bend_length[0] + s_bend_length[1] + coupling_length
    x_in1 = s_bend_length[0] - s_bend_length[1]
    y_out1 = s_bend_offset[0] + s_bend_offset[1] + coupling_distance
    x_mid = s_bend_length[0] + coupling_length
    y_mid = s_bend_offset[0] + coupling_distance

    for layer, path in port_spec[0].get_paths((0, 0)):
        path.s_bend((s_bend_length[0], s_bend_offset[0]), euler_fraction)
        if coupling_length > 0:
            path.segment((x_mid, s_bend_offset[0]))
        path.s_bend((x_out0, 0), euler_fraction)
        c.add(layer, path)

    for layer, path in port_spec[1].get_paths((x_out1, y_out1)):
        path.s_bend((x_mid, y_mid), euler_fraction, direction=(-1, 0))
        if coupling_length > 0:
            path.segment((s_bend_length[0], y_mid))
        path.s_bend((x_in1, y_out1), euler_fraction)
        c.add(layer, path)

    c.add_port(_pf.Port((0, 0), 0, port_spec[0]))
    c.add_port(_pf.Port((x_in1, y_out1), 0, port_spec[1], inverted=True))
    c.add_port(_pf.Port((x_out0, 0), -180, port_spec[0], inverted=True))
    c.add_port(_pf.Port((x_out1, y_out1), 180, port_spec[1]))

    return c


@_pf.parametric_component
def s_bend_straight_coupler(
    *,
    port_spec: _PortSpecPair | None = None,
    coupling_distance: _pft.Coordinate | None = None,
    s_bend_length: _OptPositiveDimension | None = None,
    s_bend_offset: _pft.Coordinate | None = None,
    euler_fraction: _OptFraction | None = None,
    coupling_length: _OptDimension | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """S bend/straight coupling region.

    Args:
        port_spec: Port specification describing waveguide cross-section.
          A tuple with 2 values can be used, one for each coupler side.
        coupling_distance: Distance between waveguide centers.
        s_bend_length: Length of the S bends.
        s_bend_offset: Offset of the S bends.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        coupling_length: Length of straight coupling region. If ``None``,
          defaults to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.Tidy3DModel` is used.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.

    Returns:
        Coupling component.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "s_bend_straight_coupler"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = (technology.ports[port_spec], technology.ports[port_spec])
    elif isinstance(port_spec, _pf.PortSpec):
        port_spec = (port_spec, port_spec)
    else:
        port_spec = list(port_spec)
        for i in range(2):
            if isinstance(port_spec[i], str):
                port_spec[i] = technology.ports[port_spec[i]]

    coupling_distance = _get_default(function, "coupling_distance", coupling_distance)

    s_bend_offset = _get_default(function, "s_bend_offset", s_bend_offset)
    default_length = None
    if s_bend_length is None:
        abs_offset = abs(s_bend_offset)
        radius = _get_default("bend", "radius", None, port_spec[1].default_radius)
        if 4 * radius > abs_offset:
            default_length = _pf.s_bend_length(abs_offset, radius)

    s_bend_length = _get_default(function, "s_bend_length", s_bend_length, default_length)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    coupling_length = _get_default(function, "coupling_length", coupling_length, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _Tidy3DModel())

    if tidy3d_model_kwargs is not None:
        _warn.warn(
            "Argument 'tidy3d_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        model = _Tidy3DModel(**dict(tidy3d_model_kwargs))

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "dc"
    c.add_model(model)

    xs = 2 * s_bend_length + coupling_length
    for layer, path in port_spec[0].get_paths((0, 0)):
        c.add(layer, path.segment((xs, 0)))

    x_mid = s_bend_length + coupling_length
    ys = s_bend_offset + coupling_distance
    for layer, path in port_spec[1].get_paths((xs, ys)):
        path.s_bend((x_mid, coupling_distance), euler_fraction, direction=(-1, 0))
        if coupling_length > 0:
            path.segment((s_bend_length, coupling_distance))
        path.s_bend((0, ys), euler_fraction)
        c.add(layer, path)

    c.add_port(_pf.Port((0, 0), 0, port_spec[0]))
    c.add_port(_pf.Port((0, ys), 0, port_spec[1], inverted=True))
    c.add_port(_pf.Port((xs, 0), -180, port_spec[0], inverted=True))
    c.add_port(_pf.Port((xs, ys), 180, port_spec[1]))

    return c


def _rectangular_spiral_geometry(
    turns,
    radius,
    separation,
    size,
    align_ports,
    technology,
    name,
    straight_kwds,
    bend0,
    bend1,
):
    if align_ports == "x":
        inner_size = [size[0] - 2 * separation, size[1] - separation]
    elif align_ports == "y":
        inner_size = [size[0] - 2 * separation - radius, size[1]]
    else:
        inner_size = [size[0] - 2 * separation, size[1]]

    if turns % 2 == 0:
        inner_size = [inner_size[1], inner_size[0]]

    inner_size[0] -= 4 * radius + ((turns - 2) // 2) * 2 * separation
    inner_size[1] -= 2 * radius + ((turns - 1) // 2) * 2 * separation

    for i in range(2):
        if inner_size[i] < 0:
            j = (1 - i) if turns % 2 == 0 else i
            if size[j] > 0:
                raise ValueError(
                    f"Dimension {size[j]} is too small for the spiral in the {'xy'[j]} axis."
                )
            inner_size[i] = 0

    straight = _straight(length=inner_size[1], **straight_kwds)
    p0, p1 = sorted(straight.ports)

    c = _pf.Component(name, technology=technology)

    start = c.add_reference(straight)
    if turns % 4 == 1:
        start.rotate(90)
    elif turns % 4 == 2:
        start.rotate(180)
    elif turns % 4 == 3:
        start.rotate(-90)
    arm0 = start
    arm1 = start

    lengths = [inner_size[0] / 2, inner_size[1] + separation]
    for steps in range(turns):
        arm0 = c.add_reference(bend0).connect(p0, arm0[p1])
        arm1 = c.add_reference(bend1).connect(p1, arm1[p0])
        i = steps % 2
        if steps < turns - 1 and lengths[i] > 0:
            straight = _straight(length=lengths[i], **straight_kwds)
            arm0 = c.add_reference(straight).connect(p0, arm0[p1])
            arm1 = c.add_reference(straight).connect(p1, arm1[p0])
        if steps == 0:
            lengths[0] += inner_size[0] / 2 + separation + 2 * radius
        else:
            lengths[i] += 2 * separation

    straight = _straight(length=lengths[(turns + 1) % 2] - 2 * separation + radius, **straight_kwds)
    arm1 = c.add_reference(straight).connect(p1, arm1[p0])

    if align_ports == "x":
        straight = _straight(length=lengths[(turns + 1) % 2] - 2 * separation, **straight_kwds)
        arm0 = c.add_reference(straight).connect(p0, arm0[p1])
        arm0 = c.add_reference(bend0).connect(p0, arm0[p1])
        straight = _straight(length=lengths[turns % 2], **straight_kwds)
        arm0 = c.add_reference(straight).connect(p0, arm0[p1])
        arm0 = c.add_reference(bend0).connect(p0, arm0[p1])
        straight = _straight(length=lengths[(turns + 1) % 2] - separation + radius, **straight_kwds)
        arm0 = c.add_reference(straight).connect(p0, arm0[p1])
    elif align_ports == "y":
        straight = _straight(length=lengths[(turns + 1) % 2] - 2 * separation, **straight_kwds)
        arm0 = c.add_reference(straight).connect(p0, arm0[p1])
        arm0 = c.add_reference(bend0).connect(p0, arm0[p1])
        straight = _straight(length=lengths[turns % 2] - separation, **straight_kwds)
        arm0 = c.add_reference(straight).connect(p0, arm0[p1])
        arm0 = c.add_reference(bend1).connect(p0, arm0[p1])
    else:
        arm0 = c.add_reference(straight).connect(p0, arm0[p1])

    if inner_size[1] == 0:
        c.remove(start)

    dx = -arm1[p0].center
    for ref in c.references:
        ref.translate(dx)

    p0 = c.add_port(arm1[p0])
    p1 = c.add_port(arm0[p1])
    return c, p0, p1


@_pf.parametric_component
def rectangular_spiral(
    *,
    port_spec: _pft.PortSpecOrName | None = None,
    turns: _OptIntTurns | None = None,
    radius: _pft.PositiveDimension | None = None,
    separation: _OptDimension | None = None,
    size: _OptDimension2D | None = None,
    full_length: _OptPositiveDimension = None,
    align_ports: _OptAxis | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    straight_kwargs: _pft.kwargs_for(straight, optional=True) | None = None,
    bend_kwargs: _pft.kwargs_for(bend, optional=True) | None = None,
    active_model: _pft.annotate(_typ.Literal["Tidy3D", "Circuit"], optional=True, deprecated=True)
    | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
    circuit_model_kwargs: _pft.kwargs_for(_CircuitModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Rectangular spiral.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        turns: Number of turns in each of the 2 spiral arms.
        radius: Bend radius for the spiral turns.
        separation: Distance between waveguide centers in parallel sections.
          If ``None``, defaults to the port width.
        size: Spiral dimensions measured from the waveguide centers. If
          ``None``, defaults to ``(0, 0)``.
        full_length: Desired spiral length. If set to a positive value,
          'turns' and 'size[1]' are calculated automatically.
        align_ports: Optionally align ports to have centers with same
          ``"x"`` or ``"y"`` coordinates.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.CircuitModel` is used.
        straight_kwargs: Dictionary of keyword arguments for
          :func:`straight`.
        bend_kwargs: Dictionary of keyword arguments for :func:`bend`.
        active_model: *(DEPRECATED)* Name of the model to be used by
          default; must be either ``"Tidy3D"`` or ``"Circuit"``.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.
        circuit_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.CircuitModel`.

    Returns:
        Component with path sections, ports and model.

    Note:
        The full length of the spiral can be computed with the
        :func:`photonforge.route_length` function.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "rectangular_spiral"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    radius = _get_default(
        function,
        "radius",
        radius,
        port_spec.default_radius if port_spec.default_radius > 0 else None,
    )

    turns = _get_default(function, "turns", turns, 0)
    separation = _get_default(function, "separation", separation, 0)
    size = _get_default(function, "size", size, (0, 0))
    full_length = _get_default(function, "full_length", full_length, 0)
    align_ports = _get_default(function, "align_ports", align_ports, "")
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _CircuitModel())
    straight_kwargs = dict(_get_default(function, "straight_kwargs", straight_kwargs, {}))
    bend_kwargs = dict(_get_default(function, "bend_kwargs", bend_kwargs, {}))

    if (
        active_model is not None
        or tidy3d_model_kwargs is not None
        or circuit_model_kwargs is not None
    ):
        _warn.warn(
            "Arguments 'active_model', 'tidy3d_model_kwargs', and 'circuit_model_kwargs' are "
            "deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        active_model = _get_default(function, "active_model", active_model, "Circuit")
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        circuit_model_kwargs = _get_default(
            function, "circuit_model_kwargs", circuit_model_kwargs, {}
        )

        if active_model == "Circuit":
            model = _CircuitModel(**circuit_model_kwargs)
        else:
            model_kwargs = {"port_symmetries": [(1, 0)]}
            model_kwargs.update(tidy3d_model_kwargs)
            model = _Tidy3DModel(**model_kwargs)

    straight_kwargs["technology"] = technology
    straight_kwargs["port_spec"] = port_spec
    straight_kwargs.pop("length", None)

    bend_kwargs["technology"] = technology
    bend_kwargs["port_spec"] = port_spec
    bend_kwargs["radius"] = radius

    if full_length <= 0 and turns < 2:
        raise ValueError("Argument 'turns' must be at least 2.")

    if separation <= 0:
        separation = port_spec.width

    if align_ports == "none":
        align_ports = ""
    if align_ports not in ("x", "y", ""):
        raise ValueError("Argument 'align_ports' must be one of 'x', 'y', 'none', or ''.")

    bend_kwargs["angle"] = -90
    bend0 = _bend(**bend_kwargs)
    bend_kwargs["angle"] = 90
    bend1 = _bend(**bend_kwargs)
    args = [radius, separation, size, align_ports, technology, name, straight_kwargs, bend0, bend1]

    if full_length > 0:
        if turns != 0:
            _warn.warn(
                "When 'full_length' is specified, argument 'turns' has no effect.",
                RuntimeWarning,
                3,
            )
        # Calculate turns and size[1]
        t0 = 2
        c0, p0, _ = _rectangular_spiral_geometry(t0, *args)
        l0 = _pf.route_length(c0)
        if l0 > full_length:
            raise RuntimeError(f"Length {full_length} μm is too short for the current bend radius.")

        t1 = 3
        c1, *_ = _rectangular_spiral_geometry(t1, *args)
        l1 = _pf.route_length(c1)
        while l1 <= full_length:
            t0 = t1
            c0 = c1
            l0 = l1
            t1 *= 2
            c1, *_ = _rectangular_spiral_geometry(t1, *args)
            l1 = _pf.route_length(c1)

        x = (full_length - l0) / (l1 - l0)
        turns = min(t1 - 1, max(t0 + 1, int(0.5 + t0 * (1.0 - x) + t1 * x)))
        while t1 - t0 > 1:
            c, *_ = _rectangular_spiral_geometry(turns, *args)
            new_len = _pf.route_length(c)
            if new_len <= full_length:
                l0 = new_len
                t0 = turns
                c0 = c
            else:
                l1 = new_len
                t1 = turns
            x = (full_length - l0) / (l1 - l0)
            turns = min(t1 - 1, max(t0 + 1, int(0.5 + t0 * (1.0 - x) + t1 * x)))
        turns = t0

        arms = (1 + turns) // 2 * 2
        if align_ports == "":
            arms -= 1

        ymax = ymin = c0[p0].center[1]
        for reference in c0.references:
            for port_list in reference.get_ports().values():
                for port in port_list:
                    y = port.center[1]
                    ymin = min(ymin, y)
                    ymax = max(ymax, y)

        err = full_length - l0
        args[2] = (size[0], (ymax - ymin) + err / arms)

    c, _, _ = _rectangular_spiral_geometry(turns, *args)
    c.properties.__thumbnail__ = "wg"
    c.add_model(model)

    return c


def _spiral_expression(turns, r_min, delta_r, phi0, inwards):
    phi0 *= _np.pi / 180

    if inwards:
        r0 = r_min + turns * delta_r
    else:
        r0 = r_min
        turns = -turns

    dr = -turns * delta_r
    dphi = 2 * _np.pi * turns
    return _pf.Expression(
        "u",
        [
            ("phi", f"{phi0} + u * {dphi}"),
            ("r", f"{r0} + u * {dr}"),
            ("x0", r0 * _np.cos(phi0)),
            ("y0", r0 * _np.sin(phi0)),
            ("x", "r * cos(phi) - x0"),  # make sure the path starts at (0, 0)
            ("y", "r * sin(phi) - y0"),
            ("dx_du", f"{dr} * cos(phi) - r * sin(phi) * {dphi}"),
            ("dy_du", f"{dr} * sin(phi) + r * cos(phi) * {dphi}"),
        ],
    )


def _circular_spiral_geometry(turns, port_spec, radius, separation, align_ports, name, technology):
    c = _pf.Component(name, technology=technology)

    delta_r = 2 * separation
    straight_length = radius + turns * delta_r + separation
    center = (
        straight_length,
        2 * (radius + ((turns + 0.5) if align_ports else turns) * separation),
    )
    path_end = (
        (0, separation) if align_ports else (2 * straight_length, 4 * (radius + turns * separation))
    )

    max_evals = max(10000, int(1000 * radius * turns))

    path_length = 0
    for layer, path in port_spec.get_paths((0, 0)):
        # It is important to have an "well-behaved" path section before and after the parametric
        # section because the gradient vector of the spiral is not perfectly aligned to the y axis
        # neither at the beginning nor at the end of the spiral, which can lead to discontinuities
        # in the GDSII when joining another path section.
        if straight_length > 0:
            path.segment((straight_length, 0))
        if align_ports:
            path.parametric(
                _spiral_expression(turns + 0.5, 2 * radius, delta_r, -90, True), max_evals=max_evals
            )
            angle = (-90 + 360 * (turns + 0.5)) % 360
        elif turns > 0:
            path.parametric(
                _spiral_expression(turns, 2 * radius, delta_r, -90, True), max_evals=max_evals
            )
            angle = (-90 + 360 * turns) % 360
        else:
            angle = -90
        path.arc(angle, angle + 180, radius, euler_fraction=0.0, endpoint=center)
        path.arc(angle, angle - 180, radius, euler_fraction=0.0)
        if turns > 0:
            path.parametric(
                _spiral_expression(turns, 2 * radius, delta_r, angle + 180, False),
                max_evals=max_evals,
            )
        if straight_length > 0:
            path.segment(path_end)
        c.add(layer, path)
        if path_length == 0:
            path_length = path.length()

    return c, path_length, path_end


@_pf.parametric_component
def circular_spiral(
    *,
    port_spec: _pft.PortSpecOrName | None = None,
    turns: _OptDimension | None = None,
    radius: _pft.PositiveDimension | None = None,
    separation: _OptDimension | None = None,
    full_length: _OptPositiveDimension = None,
    align_ports: _OptBool | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    active_model: _pft.annotate(_typ.Literal["Tidy3D", "Waveguide"], optional=True, deprecated=True)
    | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
    waveguide_model_kwargs: _pft.kwargs_for(_WaveguideModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Circular spiral.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        turns: Number of turns in each of the 2 spiral arms. Does not need
          to be an integer.
        radius: Bend radius for the internal spiral turns.
        separation: Distance between waveguide centers in parallel sections.
          If ``None``, defaults to the port width.
        full_length: Desired spiral length. If set to a positive value,
          'turns' is calculated automatically.
        align_ports: Optionally align ports on the same side of the spiral.
          If ``None``, defaults to ``False``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.WaveguideModel` is used.
        active_model: *(DEPRECATED)* Name of the model to be used by
          default; must be either ``"Tidy3D"`` or ``"Waveguide"``.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.
        waveguide_model_kwargs: *(DEPRECATED)* Dictionary of keyword
          arguments passed to the component's
          :class:`photonforge.WaveguideModel`.

    Returns:
        Component with the spiral section, ports and model.

    Note:
        The full length of the spiral can be computed with the
        :func:`photonforge.route_length` function.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "circular_spiral"
    port_spec = _get_default(function, "port_spec", port_spec)
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    radius = _get_default(
        function,
        "radius",
        radius,
        port_spec.default_radius if port_spec.default_radius > 0 else None,
    )

    turns = _get_default(function, "turns", turns, 0)
    separation = _get_default(function, "separation", separation, 0)
    full_length = _get_default(function, "full_length", full_length, 0)
    align_ports = _get_default(function, "align_ports", align_ports, False)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _WaveguideModel())

    if (
        active_model is not None
        or tidy3d_model_kwargs is not None
        or waveguide_model_kwargs is not None
    ):
        _warn.warn(
            "Arguments 'active_model', 'tidy3d_model_kwargs', and 'waveguide_model_kwargs' are "
            "deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        active_model = _get_default(function, "active_model", active_model, "Waveguide")
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        waveguide_model_kwargs = _get_default(
            function, "waveguide_model_kwargs", waveguide_model_kwargs, {}
        )
        if active_model == "Waveguide":
            model = _WaveguideModel(**dict(waveguide_model_kwargs))
        else:
            model_kwargs = {"port_symmetries": [(1, 0)]}
            model_kwargs.update(tidy3d_model_kwargs)
            model = _Tidy3DModel(**model_kwargs)

    if full_length <= 0 and turns <= 0:
        raise ValueError("Argument 'turns' must be positive.")

    if separation <= 0:
        separation = port_spec.width

    args = (port_spec, radius, separation, align_ports, name, technology)

    if full_length > 0:
        if turns > 0:
            _warn.warn(
                "When 'full_length' is specified, argument 'turns' has no effect.",
                RuntimeWarning,
                3,
            )

        t0 = 0
        _, l0, _ = _circular_spiral_geometry(t0, *args)
        if l0 > full_length:
            raise RuntimeError(f"Length {full_length} μm is too short for the current bend radius.")

        t1 = 1
        _, l1, _ = _circular_spiral_geometry(t1, *args)
        while l1 < full_length:
            t0 = t1
            l0 = l1
            t1 *= 2
            _, l1, _ = _circular_spiral_geometry(t1, *args)

        x = (full_length - l0) / (l1 - l0)
        turns = t0 * (1.0 - x) + t1 * x
        c, path_length, path_end = _circular_spiral_geometry(turns, *args)
        while abs(full_length - path_length) > _pf.config.tolerance * 0.5:
            if path_length < full_length:
                l0 = path_length
                t0 = turns
            else:
                l1 = path_length
                t1 = turns
            x = (full_length - l0) / (l1 - l0)
            turns = t0 * (1.0 - x) + t1 * x
            c, path_length, path_end = _circular_spiral_geometry(turns, *args)
    else:
        c, path_length, path_end = _circular_spiral_geometry(turns, *args)

    c.properties.__thumbnail__ = "wg"
    c.add_model(model)

    c.add_port(_pf.Port((0, 0), 0, port_spec))
    c.add_port(_pf.Port(path_end, 0 if align_ports else 180, port_spec))

    return c


def _get_port_or_terminal(
    arg: _pf.Port | _pf.Terminal | tuple[_pf.Reference, str] | tuple[_pf.Reference, str, int],
    get_ports: bool,
) -> _pf.Port:
    n = "port" if get_ports else "terminal"
    error = TypeError(
        f"Argument '{n}*' must be a {n.capitalize()} instance or a tuple with a Reference, the "
        f"{n} name, and, optionally, the reference index in case of a reference array."
    )

    if isinstance(arg, _pf.Port):
        if not get_ports:
            raise error
        return arg

    if isinstance(arg, _pf.Terminal):
        if get_ports:
            raise error
        return arg

    len_arg = len(arg)
    if (
        len_arg < 2
        or len_arg > 3
        or not isinstance(arg[0], _pf.Reference)
        or not isinstance(arg[1], str)
        or (len_arg == 3 and not isinstance(arg[2], int))
    ):
        raise error

    if get_ports:
        return arg[0].get_ports(arg[1])[0 if len_arg == 2 else arg[2]]
    return arg[0].get_terminals(arg[1])[0 if len_arg == 2 else arg[2]]


@_pf.parametric_component
def route(
    *,
    port1: _Port | None = None,
    port2: _Port | None = None,
    radius: _pft.PositiveDimension | None = None,
    waypoints: _OptCoords | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    straight_kwargs: _pft.kwargs_for(straight, optional=True) | None = None,
    bend_kwargs: _pft.kwargs_for(bend, optional=True) | None = None,
    s_bend_kwargs: _pft.kwargs_for(s_bend, optional=True) | None = None,
    circuit_model_kwargs: _pft.kwargs_for(_CircuitModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Route the connection between 2 compatible ports.

    The route is built heuristically from :func:`straight`, :func:`bend`,
    and :func:`s_bend` sections, favoring Manhattan geometry.

    Args:
        port1: First port to be connected. The port can be specfied as a
          :class:`photonforge.Port` or as a tuple including a
          :class:`photonforge.Reference`, the port name, and the repetition
          index (optional, only for array references).
        port2: Second port to be connected.
        radius: Radius used for bends.
        waypoints: 2D coordinates used to guide the route (see note).
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.CircuitModel` is used.
        straight_kwargs: Keyword arguments for :func:`straight`.
        bend_kwargs: Keyword arguments for :func:`bend`.
        s_bend_kwargs: Keyword arguments for :func:`s_bend`.
        circuit_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.CircuitModel`.

    Returns:
        Component with the route, including ports and model.

    Note:
        Each waypoint can also include the route direction at that point by
        including the angle (in degrees). Angles must be a multiple of 90°.
    """
    if technology is None:
        technology = _pf.config.default_technology

    function = "route"
    port1 = _get_default(function, "port1", port1)
    port2 = _get_default(function, "port2", port2)

    port1 = _get_port_or_terminal(port1, True)
    port2 = _get_port_or_terminal(port2, True)

    if not port1.can_connect_to(port2):
        raise RuntimeError("Ports have incompatible specifications and cannot be connected.")

    port_spec = port1.spec if port1.inverted else port1.spec.inverted()

    radius = _get_default(function, "radius", radius, ())
    waypoints = _get_default(function, "waypoints", waypoints, ())
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _CircuitModel())
    straight_kwargs = dict(_get_default(function, "straight_kwargs", straight_kwargs, {}))
    bend_kwargs = dict(_get_default(function, "bend_kwargs", bend_kwargs, {}))
    s_bend_kwargs = dict(_get_default(function, "s_bend_kwargs", s_bend_kwargs, {}))

    if circuit_model_kwargs is not None:
        _warn.warn(
            "Argument 'circuit_model_kwargs' is deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        circuit_model_kwargs = _get_default(
            function, "circuit_model_kwargs", circuit_model_kwargs, {}
        )
        model = _CircuitModel(**dict(circuit_model_kwargs))

    straight_kwargs["technology"] = technology
    straight_kwargs["port_spec"] = port_spec

    bend_kwargs["technology"] = technology
    bend_kwargs["port_spec"] = port_spec
    if radius != ():
        bend_kwargs["radius"] = radius

    s_bend_kwargs["technology"] = technology
    s_bend_kwargs["port_spec"] = port_spec

    wp = _np.empty((len(waypoints), 3))
    for i, p in enumerate(waypoints):
        wp[i, 0] = p[0]
        wp[i, 1] = p[1]
        wp[i, 2] = p[2] % 360 if len(p) > 2 else -1

    component = _pf.Component(name, technology=technology)
    component.properties.__thumbnail__ = "wg"
    component.add_model(model)

    dir0 = (port1.input_direction + 180) % 360
    p0 = _pf.Port(port1.center, dir0, port1.spec, inverted=not port1.inverted)
    dir1 = (port2.input_direction + 180) % 360
    p1 = _pf.Port(port2.center, dir1, port2.spec, inverted=not port2.inverted)
    component.add_port([p0, p1])

    return _pf.extension._route(
        component,
        radius,
        wp,
        _straight,
        straight_kwargs,
        _bend,
        bend_kwargs,
        _s_bend,
        s_bend_kwargs,
    )


@_pf.parametric_component
def route_s_bend(
    *,
    port1: _Port | None = None,
    port2: _Port | None = None,
    euler_fraction: _OptFraction | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
    model: _OptModel | None = None,
    active_model: _pft.annotate(_typ.Literal["Tidy3D", "Waveguide"], optional=True, deprecated=True)
    | None = None,
    tidy3d_model_kwargs: _pft.kwargs_for(_Tidy3DModel, optional=True, deprecated=True)
    | None = None,
    waveguide_model_kwargs: _pft.kwargs_for(_WaveguideModel, optional=True, deprecated=True)
    | None = None,
) -> _pf.Component:
    """Create an S bend connecting 2 compatible ports.

    Args:
        port1: First port to be connected. The port can be specfied as a
          :class:`photonforge.Port` or as a tuple including a
          :class:`photonforge.Reference`, the port name, and the repetition
          index (optional, only for array references).
        port2: Second port to be connected.
        euler_fraction: Fraction of the bends that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`). If ``None``, defaults
          to 0.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component. If ``None`` a
          :class:`photonforge.WaveguideModel` is used.
        active_model: *(DEPRECATED)* Name of the model to be used by
          default; must be either ``"Tidy3D"`` or ``"Waveguide"``.
        tidy3d_model_kwargs: *(DEPRECATED)* Dictionary of keyword arguments
          passed to the component's :class:`photonforge.Tidy3DModel`.
        waveguide_model_kwargs: *(DEPRECATED)* Dictionary of keyword
          arguments passed to the component's
          :class:`photonforge.WaveguideModel`.

    Returns:
        Component with the route, including ports and model.
    """
    function = "route_s_bend"
    port1 = _get_default(function, "port1", port1)
    port2 = _get_default(function, "port2", port2)
    euler_fraction = _get_default(function, "euler_fraction", euler_fraction, 0)
    name = _get_default(function, "name", name, "")
    model = _get_default(function, "model", model, _WaveguideModel())

    if (
        active_model is not None
        or tidy3d_model_kwargs is not None
        or waveguide_model_kwargs is not None
    ):
        _warn.warn(
            "Arguments 'active_model', 'tidy3d_model_kwargs', and 'waveguide_model_kwargs' are "
            "deprecated. Please use argument 'model' instead.",
            RuntimeWarning,
            3,
        )
        active_model = _get_default(function, "active_model", active_model, "Waveguide")
        tidy3d_model_kwargs = _get_default(function, "tidy3d_model_kwargs", tidy3d_model_kwargs, {})
        waveguide_model_kwargs = _get_default(
            function, "waveguide_model_kwargs", waveguide_model_kwargs, {}
        )
        if active_model == "Waveguide":
            model = _WaveguideModel(**waveguide_model_kwargs)
        else:
            model_kwargs = {"port_symmetries": [(1, 0)]}
            model_kwargs.update(tidy3d_model_kwargs)
            model = _Tidy3DModel(**model_kwargs)

    port1 = _get_port_or_terminal(port1, True)
    port2 = _get_port_or_terminal(port2, True)

    if not port1.can_connect_to(port2):
        raise RuntimeError("Ports have incompatible specifications and cannot be connected.")

    if abs((port1.input_direction - port2.input_direction) % 360 - 180) >= 1e-12:
        raise RuntimeError("Ports must have opposite directions.")

    if technology is None:
        technology = _pf.config.default_technology

    port_spec = port1.spec if port1.inverted else port1.spec.inverted()

    angle = (port1.input_direction - 180) / 180 * _np.pi
    direction = _np.array((_np.cos(angle), _np.sin(angle)))

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "wg"
    c.add_model(model)

    path_length = None
    for layer, path in port_spec.get_paths(port1.center):
        c.add(layer, path.s_bend(port2.center, euler_fraction, direction))
        if path_length is None:
            path_length = path.length()

    c.add_port(_pf.Port(port1.center, port1.input_direction - 180, port_spec))
    c.add_port(_pf.Port(port2.center, port2.input_direction - 180, port_spec, inverted=True))
    return c


@_pf.parametric_component
def route_taper(
    *,
    terminal1: _Terminal | None = None,
    terminal2: _Terminal | None = None,
    layer: _OptLayer | None = None,
    offset_distance: _OptOffsets | None = None,
    use_box: _OptBool | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
):
    """Create a taper connecting 2 terminals.

    Args:
        terminal1: First terminal to be connected. The terminal can be
          specified as a :class:`photonforge.Terminal` or as a tuple
          including a :class:`photonforge.Reference`, the terminal name, and
          the repetition index (optional, only for array references).
        terminal2: Second terminal to be connected.
        layer: Layer used for the connection. If ``None``, the routing layer
          of the first terminal is used.
        offset_distance: Offset applied to the terminal structure before
          creating the envelope taper. If ``None``, defaults to 0.
        use_box: Flag indicating whether to use the bounding box of the
          terminal structures or the structures themselves. If ``None``,
          defaults to ``True``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        Component with the route.
    """
    function = "route_taper"
    terminal1 = _get_default(function, "terminal1", terminal1)
    terminal2 = _get_default(function, "terminal2", terminal2)
    layer = _get_default(function, "layer", layer, ())
    offset_distance = _get_default(function, "offset_distance", offset_distance, 0)
    use_box = _get_default(function, "use_box", use_box, True)
    name = _get_default(function, "name", name, "")

    terminal1 = _get_port_or_terminal(terminal1, False)
    terminal2 = _get_port_or_terminal(terminal2, False)

    if layer == ():
        layer = terminal1.routing_layer
        if terminal1.routing_layer != terminal2.routing_layer:
            _warn.warn(
                f"Terminals have different routing layers. Using {layer}.", RuntimeWarning, 3
            )

    if hasattr(offset_distance, "__float__"):
        offset_distance = (offset_distance, offset_distance)

    structure1 = terminal1.structure
    if use_box:
        structure1 = _pf.Rectangle(*structure1.bounds())
        a, b = structure1.size
        structure1.size = (max(0, a + 2 * offset_distance[0]), max(0, b + 2 * offset_distance[0]))
    else:
        if offset_distance[0] < 0:
            structure1 = _pf.offset(structure1, offset_distance[0])
        if offset_distance[0] != 0:
            structure1 = _pf.envelope(structure1, max(0, offset_distance[0]))

    structure2 = terminal2.structure
    if use_box:
        structure2 = _pf.Rectangle(*structure2.bounds())
        a, b = structure2.size
        structure2.size = (max(0, a + 2 * offset_distance[1]), max(0, b + 2 * offset_distance[1]))
    else:
        if offset_distance[1] < 0:
            structure2 = _pf.offset(structure2, offset_distance[1])
        if offset_distance[1] != 0:
            structure2 = _pf.envelope(structure2, max(0, offset_distance[1]))

    min1, max1 = structure1.bounds()
    min2, max2 = structure2.bounds()
    size1 = max1 - min1
    size2 = max2 - min2

    prefer_x = (size1[0] < _pf.config.grid) or (size2[0] < _pf.config.grid)
    prefer_y = (size1[1] < _pf.config.grid) or (size2[1] < _pf.config.grid)

    if prefer_x == prefer_y:
        distance = (max2 + min2) - (max1 + min1)
        prefer_x = abs(distance[0]) > abs(distance[1])
        # prefer_y = not prefer_x  (unused)

    overlap_x = not (max1[0] < min2[0] or max2[0] < min1[0])
    overlap_y = not (max1[1] < min2[1] or max2[1] < min1[1])

    if (overlap_x and overlap_y) or not use_box:
        taper = _pf.envelope([structure1, structure2])
    elif overlap_y or (not overlap_x and prefer_x):
        if max2[0] < min1[0]:
            structure1, structure2 = structure2, structure1
            min1, min2 = min2, min1
            max1, max2 = max2, max1
        taper = _pf.Polygon(
            (
                max1,
                (min1[0], max1[1]),
                min1,
                (max1[0], min1[1]),
                min2,
                (max2[0], min2[1]),
                max2,
                (min2[0], max2[1]),
            )
        )
    else:
        if max2[1] < min1[1]:
            structure1, structure2 = structure2, structure1
            min1, min2 = min2, min1
            max1, max2 = max2, max1
        taper = _pf.Polygon(
            (
                (min1[0], max1[1]),
                min1,
                (max1[0], min1[1]),
                max1,
                (max2[0], min2[1]),
                max2,
                (min2[0], max2[1]),
                min2,
            )
        )

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "connection"

    c.add(layer, taper)
    return c


@_pf.parametric_component
def route_manhattan(
    *,
    terminal1: _Terminal | None = None,
    terminal2: _Terminal | None = None,
    direction1: _OptAxis | None = None,
    direction2: _OptAxis | None = None,
    layer: _OptLayer | None = None,
    width: _OptPositiveDimension | None = None,
    overlap_fraction: _OptFractions | None = None,
    join_limit: _OptJoin | None = None,
    waypoints: _OptCoords | None = None,
    technology: _OptTechnology | None = None,
    name: _OptStr | None = None,
):
    """Create a Manhattan path connecting 2 terminals.

    Args:
        terminal1: First terminal to be connected. The terminal can be
          specified as a :class:`photonforge.Terminal` or as a tuple
          including a :class:`photonforge.Reference`, the terminal name, and
          the repetition index (optional, only for array references).
        terminal2: Second terminal to be connected.
        direction1: Direction (`""`, `"x"`, or `"y"`) of the route at the
          first terminal.
        direction2: Direction (`""`, `"x"`, or `"y"`) of the route at the
          second terminal.
        layer: Layer used for the connection. If ``None``, the routing layer
          of the first terminal is used.
        width: Width of the routing path. If ``None``, the width is derived
          from the bounding box of the first terminal.
        overlap_fraction: Fraction of the terminal bounding box that the
          route overlaps.  If ``None``, defaults to 1.
        join_limit: Join limit used by :func:`photonforge.Path.segment`. If
          ``None`` defaults to -1.
        waypoints: Sequence of coordinates the route should go through.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        Component with the route.
    """
    function = "route_manhattan"
    terminal1 = _get_default(function, "terminal1", terminal1)
    terminal2 = _get_default(function, "terminal2", terminal2)
    direction1 = _get_default(function, "direction1", direction1, "")
    direction2 = _get_default(function, "direction2", direction2, "")
    layer = _get_default(function, "layer", layer, ())
    width = _get_default(function, "width", width, -1)
    overlap_fraction = _get_default(function, "overlap_fraction", overlap_fraction, 1)
    join_limit = _get_default(function, "join_limit", join_limit, -1)
    waypoints = _get_default(function, "waypoints", waypoints, ())
    name = _get_default(function, "name", name, "")

    terminal1 = _get_port_or_terminal(terminal1, False)
    terminal2 = _get_port_or_terminal(terminal2, False)

    if layer == ():
        layer = terminal1.routing_layer
        if terminal1.routing_layer != terminal2.routing_layer:
            _warn.warn(
                f"Terminals have different routing layers. Using {layer}.", RuntimeWarning, 3
            )

    if hasattr(overlap_fraction, "__float__"):
        overlap_fraction = (overlap_fraction, overlap_fraction)

    centers = [None, None]
    sizes = [None, None]
    directions = [-1, -1]
    for i, (terminal, direction) in enumerate(((terminal1, direction1), (terminal2, direction2))):
        min_, max_ = terminal.structure.bounds()
        sizes[i] = max_ - min_
        centers[i] = 0.5 * (min_ + max_)
        if direction == "x":
            directions[i] = 0
        elif direction == "y":
            directions[i] = 1
        elif sizes[i][0] < _pf.config.grid and sizes[i][1] >= _pf.config.grid:
            directions[i] = 0
        elif sizes[i][1] < _pf.config.grid and sizes[i][0] >= _pf.config.grid:
            directions[i] = 1

    endpoints = _pf.extension._manhatan_path(
        centers[0], centers[1], directions[0], directions[1], waypoints
    )

    direction = 1 if endpoints[0][0] == endpoints[1][0] else 0
    delta = sizes[0][direction] * (0.5 - overlap_fraction[0])
    endpoints[0][direction] += (
        delta if endpoints[0][direction] < endpoints[1][direction] else -delta
    )

    if width < 0:
        width = sizes[0][1 - direction]

    direction = 1 if endpoints[-1][0] == endpoints[-2][0] else 0
    delta = sizes[1][direction] * (0.5 - overlap_fraction[1])
    endpoints[-1][direction] += (
        delta if endpoints[-1][direction] < endpoints[-2][direction] else -delta
    )

    c = _pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "connection"

    c.add(layer, _pf.Path(endpoints[0], width).segment(endpoints[1:], join_limit=join_limit))
    return c


_straight = straight
_bend = bend
_s_bend = s_bend
