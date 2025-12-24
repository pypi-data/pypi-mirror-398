import base64
import functools
import hashlib
import warnings
from collections.abc import Callable
from typing import Any

from .extension import (
    Component,
    Expression,
    Interpolator,
    PoleResidueMatrix,
    Technology,
    _component_registry,
    _content_repr,
    _technology_registry,
)

_warnings_cache: set = set()

_gdsii_safe_chars: set[str] = set(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_?$"
)


def _safe_hash(b: bytes) -> str:
    # Remove 4 bytes of padding at the end and use a case-insensitive alphabet
    return base64.b32encode(hashlib.sha256(b).digest())[:-4].decode("utf-8")


# Tidy3D limits the path name to 100 characters, but the ui also appends the timestamp
def _filename_cleanup(s: str, strict: bool = True, max_length: int = 64) -> str:
    if strict:
        allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ()-._~")
    else:
        allowed = set(
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&'()+,-.;=@[]^_`{}~ "
        )
    result = ("".join(c if c in allowed else "" for c in s)).strip()
    if max_length > 0:
        result = result[:max_length]
    return result


def _make_str(x: Any) -> str:
    return (
        f"{x.__name__}${hash(x)}"
        if callable(x) and not isinstance(x, (PoleResidueMatrix, Expression, Interpolator))
        else str(x)
    )


def _suffix_from_args(*args: Any, **kwargs: Any) -> str:
    suffix = ""
    args_suffix = "_".join(_make_str(x) for x in args)
    if len(args_suffix) > 0:
        suffix += "_" + args_suffix
    kwargs_suffix = "_".join(f"{k}={_make_str(kwargs[k])}" for k in sorted(kwargs))
    if len(kwargs_suffix) > 0:
        suffix += "_" + kwargs_suffix
    if len(suffix) > 53:  # 1 + length of _safe_hash return value
        return "_" + _safe_hash(suffix[1:].encode("utf-8"))
    return suffix


def parametric_component(
    decorated_function: Callable | None = None,
    name_prefix: str | None = None,
    gdsii_safe_name: bool = True,
    use_parametric_cache_default: bool = True,
) -> Callable:
    """Decorator to create parametric components from functions.

    If the name of the created component is empty, this decorator sets it
    with name prefix and the values of the function arguments when called.

    Components can be cached to avoid duplication. They are cached based on
    the calling arguments (specifically, argument ``id``). Regardless of the
    default setting, each component can use or skip caching by setting the
    ``bool`` keyword argument ``use_parametric_cache`` in the decorated
    function call.

    Args:
        decorated_function: Function that returns a Component.
        name_prefix: Prefix for the component name. If ``None``, the
          decorated function name is used.
        gdsii_safe_name: If set, only use GDSII-safe characters in the name
          (``name_prefix`` is not modified by this flag).
        use_parametric_cache_default: Controls the default caching behavior
          for the decorated function.

    Examples:
        >>> @pf.parametric_component
        ... def straight(*, length, port_spec_name, technology):
        ...     port_spec = technology.ports[port_spec_name]
        ...     c = pf.Component(technology=technology)
        ...     for layer, path in port_spec.get_paths((0, 0)):
        ...         c.add(layer, path.segment((length, 0)))
        ...     c.add_port(pf.Port(center=(0, 0), input_direction=0, spec=port_spec))
        ...     c.add_port(pf.Port(center=(length, 0), input_direction=180, spec=port_spec))
        ...     c.add_model(pf.Tidy3DModel(port_symmetries=[(1, 0)]))
        ...     return c
        ...
        >>> technology = pf.basic_technology()
        >>> component = straight(length=5, port_spec_name="Strip", technology=technology)
        >>> print(component.name)
        straight_...

        Caching behavior:

        >>> component1 = straight(length=2, port_spec_name="Strip", technology=technology)
        >>> component2 = straight(length=2, port_spec_name="Strip", technology=technology)
        >>> component3 = straight(
        ...     length=2, port_spec_name="Strip", technology=technology, use_parametric_cache=False
        ... )
        >>> component2 == component1
        True
        >>> component2 is component1
        True
        >>> component3 == component1
        True
        >>> component3 is component1
        False

    Note:
        It is generally a good idea to force parametric components to accept
        only keyword arguments (by using the ``*`` as first argument in the
        argument list), because those are stored for future updates of the
        created component with :func:`Component.update`.

    See also:
        `Custom Parametric Components
        <../guides/Custom_Parametric_Components.ipynb>`__
    """

    def _decorator(component_func):
        _cache = {}
        prefix = component_func.__name__ if name_prefix is None else name_prefix
        full_name = f"{component_func.__module__}.{component_func.__qualname__}"
        if full_name in _component_registry:
            warnings.warn(
                f"Component function '{full_name}' previously registered will be overwritten.",
                RuntimeWarning,
                2,
            )

        @functools.wraps(component_func)
        def _component_func(*args, **kwargs):
            if len(args) > 0:
                warning_key = ("Parametric component with args", full_name)
                if warning_key not in _warnings_cache:
                    try:
                        var_names = component_func.__code__.co_varnames
                        assert len(var_names) > 0
                    except Exception:
                        var_names = ("argument1",)
                    _warnings_cache.add(warning_key)
                    warnings.warn(
                        f"Parametric component '{full_name}' called with positional arguments. "
                        f"Positional arguments are not remembered in parametric updates. Please "
                        f"use keyword arguments, e.g., '{component_func.__qualname__}"
                        f"({var_names[0]}={args[0]!r}, ...)'",
                        RuntimeWarning,
                        2,
                    )

            use_parametric_cache = kwargs.pop("use_parametric_cache", use_parametric_cache_default)

            c = component_func(*args, **kwargs)
            if not isinstance(c, Component):
                raise TypeError(
                    f"Updated object returned by parametric function '{full_name}' is not a "
                    "'Component' instance."
                )

            c.parametric_function = full_name

            final_kwargs = (
                dict(component_func.__kwdefaults__)
                if hasattr(component_func, "__kwdefaults__") and component_func.__kwdefaults__
                else {}
            )
            final_kwargs.update(kwargs)
            c.parametric_kwargs = final_kwargs

            if not c.name:
                suffix = _suffix_from_args(*args, **final_kwargs)
                if gdsii_safe_name:
                    suffix = "".join(x if x in _gdsii_safe_chars else "_" for x in suffix)
                c.name = prefix + suffix

            if use_parametric_cache:
                key = _content_repr(c, include_config=False)
                if key in _cache:
                    cached = _cache[key]
                    if c.technology is cached.technology and cached == c:
                        c = cached
                    else:
                        _cache[key] = c
                else:
                    _cache[key] = c
            return c

        _component_registry[full_name] = _component_func

        return _component_func

    if decorated_function:
        return _decorator(decorated_function)

    return _decorator


def parametric_technology(
    decorated_function: Callable | None = None,
    name_prefix: str | None = None,
    use_parametric_cache_default: bool = True,
) -> Callable:
    """Decorator to create parametric technologies from functions.

    If the name of the created technology is empty, this decorator sets it
    with name prefix and the values of the function arguments when called.

    Technologies can be cached to avoid duplication. They are cached based
    on the calling arguments (specifically, argument ``id``). Regardless of
    the default setting, each technology can use or skip caching by setting
    the ``bool`` keyword argument ``use_parametric_cache`` in the decorated
    function call.

    Args:
        decorated_function: Function that returns a Technology.
        name_prefix: Prefix for the technology name. If ``None``, the
          decorated function name is used.
        use_parametric_cache_default: Controls the default caching behavior
          for the decorated function.

    Example:
        >>> @pf.parametric_technology
        ... def demo_technology(*, thickness=0.250, sidewall_angle=0):
        ...     layers = {
        ...         "Si": pf.LayerSpec(
        ...             (1, 0), "Silicon layer", "#d2132e18", "//"
        ...         )
        ...     }
        ...     extrusion_specs = [
        ...         pf.ExtrusionSpec(
        ...             pf.MaskSpec((1, 0)),
        ...             td.Medium(permittivity=3.48**2),
        ...             (0, thickness),
        ...             sidewall_angle=sidewall_angle,
        ...         )
        ...     ]
        ...     port_specs = {
        ...         "STE": pf.PortSpec(
        ...             "Single mode strip",
        ...             1.5,
        ...             (-0.5, thickness + 0.5),
        ...             target_neff=3.48,
        ...             path_profiles=[(0.45, 0, (1, 0))],
        ...         )
        ...     }
        ...     technology = pf.Technology(
        ...         "Demo technology",
        ...         "1.0",
        ...         layers,
        ...         extrusion_specs,
        ...         port_specs,
        ...         td.Medium(permittivity=1.45**2),
        ...     )
        ...     # Add random variables to facilitate Monte Carlo runs:
        ...     technology.random_variables = [
        ...         pf.monte_carlo.RandomVariable(
        ...             "sidewall_angle", value=sidewall_angle, stdev=2
        ...         ),
        ...         pf.monte_carlo.RandomVariable(
        ...             "thickness",
        ...             value_range=[thickness - 0.01, thickness + 0.01],
        ...         ),
        ...     ]
        ...     return technology
        >>> technology = demo_technology(sidewall_angle=10, thickness=0.3)
        >>> technology.random_variables
        [RandomVariable('sidewall_angle', **{'value': 10, 'stdev': 2}),
         RandomVariable('thickness', **{'value_range': (0.29, 0.31)})]

    Note:
        It is generally a good idea to force parametric technologies to
        accept only keyword arguments (by using the ``*`` as first argument
        in the argument list), because those are stored for future updates
        of the created technology with :func:`Technology.update`.
    """

    def _decorator(technology_func):
        _cache = {}
        prefix = technology_func.__name__ if name_prefix is None else name_prefix
        full_name = f"{technology_func.__module__}.{technology_func.__qualname__}"
        if full_name in _technology_registry:
            warnings.warn(
                f"Technology function '{full_name}' previously registered will be overwritten.",
                RuntimeWarning,
                2,
            )

        @functools.wraps(technology_func)
        def _technology_func(*args, **kwargs):
            if len(args) > 0:
                warning_key = ("Parametric technology with args", full_name)
                if warning_key not in _warnings_cache:
                    _warnings_cache.add(warning_key)
                    warnings.warn(
                        f"Parametric technology '{full_name}' called with positional arguments. "
                        "Positional arguments are not remembered in parametric updates.",
                        RuntimeWarning,
                        2,
                    )

            use_parametric_cache = kwargs.pop("use_parametric_cache", use_parametric_cache_default)

            t = technology_func(*args, **kwargs)
            if not isinstance(t, Technology):
                raise TypeError(
                    f"Updated object returned by parametric function '{full_name}' is not a "
                    "'Technology' instance."
                )
            if not t.name:
                t.name = prefix + _suffix_from_args(*args, **kwargs)
            t.parametric_function = full_name

            final_kwargs = (
                dict(technology_func.__kwdefaults__)
                if hasattr(technology_func, "__kwdefaults__") and technology_func.__kwdefaults__
                else {}
            )
            final_kwargs.update(kwargs)
            t.parametric_kwargs = final_kwargs

            if use_parametric_cache:
                key = _content_repr(t, include_config=False)
                if key in _cache:
                    cached = _cache[key]
                    if cached == t:
                        t = cached
                    else:
                        _cache[key] = t
                else:
                    _cache[key] = t
            return t

        _technology_registry[full_name] = _technology_func

        return _technology_func

    if decorated_function:
        return _decorator(decorated_function)

    return _decorator
