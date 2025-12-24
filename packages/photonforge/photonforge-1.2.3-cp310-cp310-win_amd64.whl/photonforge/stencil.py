import typing as _typ

import photonforge as _pf

from .extension import (
    apodized_focused_grating,
    apodized_grating,
    cross,
    focused_grating,
    grating,
    linear_taper,
    mmi,
    ruler,
    vernier_scale,
)

_stencils = {
    "cross": cross,
    "focused_grating": focused_grating,
    "grating": grating,
    "apodized_grating": apodized_grating,
    "apodized_focused_grating": apodized_focused_grating,
    "linear_taper": linear_taper,
    "mmi": mmi,
    "ruler": ruler,
    "vernier_scale": vernier_scale,
    "text": _pf.extension.text,
}

_StencilName = _typ.Literal[
    "cross",
    "focused_grating",
    "grating",
    "apodized_grating",
    "apodized_focused_grating",
    "linear_taper",
    "mmi",
    "ruler",
    "vernier_scale",
    "text",
]


@_pf.parametric_component
def as_component(
    *,
    layer: str | _typ.Sequence,
    stencil: _StencilName,
    technology: _pf.Technology | None = None,
    **stencil_kwargs: _typ.Any,
) -> _pf.Component:
    """
    Create a parametric component from a stencil.

    Args:
        layer: Layer to be used for the stencil. In the case of stencil
          functions that return multiple structure lists (like
          :func:`vernier_scale`), one layer per list is required.
        stencil: Name of the stencil function.
        technology: Component technology. If ``None``, the default
          technology is used.
        stencil_kwargs: Keyword arguments for the stencil function.

    Returns:
        Parametric :class:`photonforge.Component`

    Note:
        The :func:`photonforge.text` function can also be used in this
        function as a stencil.

    Examples:
        >>> pf.config.default_technology = pf.basic_technology()
        >>> grating_component = pf.stencil.as_component(
        ...     layer="SLAB",
        ...     stencil="grating",
        ...     period=0.6,
        ...     num_periods=20,
        ...     width=10,
        ...     taper_length=30,
        ...     taper_width=0.5,
        ... )
        >>> scale_component = pf.stencil.as_component(
        ...     layer=("SLAB","WG_CORE"),
        ...     stencil="vernier_scale",
        ...     unit=15,
        ...     marker_length=20,
        ...     marker_width=2,
        ... )
    """
    stencil = _stencils.get(stencil, None)
    if stencil is None:
        valid_names = "', '".join(_stencils)
        raise RuntimeError(
            f"Stencil '{stencil}' does not exist. Valid stencil names are '{valid_names}'."
        )

    if technology is None:
        technology = _pf.config.default_technology

    c = _pf.Component(technology=technology)

    structures = stencil(**stencil_kwargs)

    structure_type = (_pf.Polygon, _pf.Rectangle, _pf.Circle, _pf.Path)
    group = 0 if isinstance(structures, structure_type) else len(structures)

    if group > 0 and not isinstance(structures[0], structure_type):
        # Return type is Sequence[Sequence[Structure]]
        error_msg = (
            f"Argument 'layer' must be a sequence of {len(structures)} layers for stencil "
            f"'{stencil}'."
        )
        if isinstance(layer, str) or len(layer) != len(structures):
            raise TypeError(error_msg)
    else:
        error_msg = (
            f"Argument 'layer' must be a string or a pair of integers for stencil '{stencil}'."
        )
        layer = [layer]
        structures = [structures]
        if group == 0:
            # Return type is a single structure
            structures = [structures]

    for group_layer, group_structures in zip(layer, structures, strict=False):
        try:
            c.add(group_layer, *group_structures)
        except TypeError as err:
            if err.args[0].startswith("Argument 0") and not isinstance(group_layer, str):
                raise TypeError(error_msg) from err
            else:
                raise
    return c
