import warnings
from collections.abc import Sequence
from typing import Literal

import numpy as np
import tidy3d as td

from .extension import (
    Circle,
    Component,
    MaskSpec,
    Path,
    Polygon,
    PortSpec,
    Rectangle,
    Reference,
    Technology,
    _pack_rectangles,
    config,
)

# Speed of light in vacuum (in µm/s)
C_0: float = 2.99792458e14

# Elementary charge (in C)
Q = 1.602176634e-19

# Planck's constant (in Js)
H = 6.62607015e-34


def route_length(component: Component, layer: Sequence[int] | None = None) -> float:
    """Measure the length of parametric routes.

    Internally, this funcions adds up the path lengths for all paths in the
    given component for a specific layer. If the component contains multiple
    paths, the sum of their lengths will be returned.

    Args:
        component: Component with routes to be measured.
        layer: Layer to be used to search for paths. If not set, all will be
          inspected and the largest length is returned.

    Returns:
        Total path length.

    See also:
        `Parametric routes <../parametric.rst#routing>`__
    """
    structures = component.get_structures(layer)
    if len(structures) == 0:
        return 0.0
    if layer is None:
        return max(
            sum(path.length() for path in structure_list if isinstance(path, Path))
            for structure_list in structures.values()
        )
    return sum(path.length() for path in structures if isinstance(path, Path))


def _layer_in_mask_score(layer: tuple[int, int], mask: MaskSpec) -> int:
    if mask.layer is not None:
        return 1 if mask.layer == layer else None
    operands = mask.operand1 + mask.operand2
    if mask.operation == "+":
        for inner in operands:
            score = _layer_in_mask_score(layer, inner)
            if score is not None:
                return 10 * score + len(operands)
    elif mask.operation == "*":
        for inner in operands:
            score = _layer_in_mask_score(layer, inner)
            if score is not None:
                return 20 * score + len(operands)
    elif mask.operation == "-":
        for inner in mask.operand1:
            score = _layer_in_mask_score(layer, inner)
            if score is not None:
                return 20 * score + len(operands)
    return None


_virtual_port_specs = {}


def virtual_port_spec(num_modes: int = 1, classification: str = "optical") -> PortSpec:
    """Template to generate a virtual PortSpec.

    Virtual port specs have no path profiles and can be used to help with
    schematic-driven design before any layout is created.

    Args:
        num_modes: Number of modes supported by the port.
        classification: One of ``"optical"`` or ``"electrical"``.

    Returns:
        Virtual port specification with no path profiles.
    """
    virtual = None
    if classification == "optical":
        virtual = PortSpec("Virtual spec (optical)", 1, (0, 0), num_modes)
    elif classification == "electrical":
        virtual = PortSpec(
            "Virtual spec (electrical)", 1, (0, 0), num_modes, voltage_path=[(-0.1, 0), (0.1, 0)]
        )
    cached = _virtual_port_specs.get((classification, num_modes))
    if cached != virtual:
        _virtual_port_specs[classification, num_modes] = virtual
        cached = virtual
    return cached


def cpw_spec(
    layer: str | Sequence[int],
    signal_width: float,
    gap: float,
    ground_width: float | None = None,
    description: str | None = None,
    width: float | None = None,
    limits: Sequence[float] | None = None,
    num_modes: int = 1,
    added_solver_modes: int = 0,
    target_neff: float = 4.0,
    gap_layer: None | str | Sequence[int] | None = None,
    include_ground: bool = True,
    conductor_limits: Sequence[float] | None = None,
    technology: Technology | None = None,
) -> PortSpec:
    """Template to generate a coplanar transmission line PortSpec.

    Args:
        layer: Layer used for the transmission line layout.
        signal_width: Width of the central conductor.
        gap: Distance between the central conductor and the grounds.
        ground_width: Width of the ground conductors.
        description: Description used in :attr:`PortSpec.description`.
        width: Dimension used in :attr:`PortSpec.width`.
        limits: Vertical port limits used in :attr:`PortSpec.limits`.
        num_modes: Value used for :attr:`PortSpec.num_modes`.
        added_solver_modes: Value used for
          :attr:`PortSpec.added_solver_modes`.
        target_neff: Value used for :attr:`PortSpec.target_neff`.
        gap_layer: If set, path profiles for the gap region are included in
          this layer.
        include_ground: If ``False``, ground path profiles are not included.
        conductor_limits: Lower and upper bounds of the conductor layer
          extrusion.
        technology: Technology in use. If ``None``, the default is used.

    Returns:
        PortSpec for the CPW transmission line.

    Note:
        If ``conductor_limits`` is not given, the extrusion specifications
        in ``technology`` are inspected. If an specification for the
        selected ``layer`` is found, its extrusion limits are used.
    """
    if technology is None:
        technology = config.default_technology

    if isinstance(layer, str):
        layer = technology.layers[layer].layer
    if isinstance(gap_layer, str):
        gap_layer = technology.layers[gap_layer].layer

    if conductor_limits is None:
        best_score = 1e30
        for extrusion in technology.extrusion_specs:
            medium = extrusion.get_medium("electrical")
            if not (medium.is_pec or isinstance(medium, td.LossyMetalMedium)):
                continue

            if extrusion.mask_spec.layer == layer:
                conductor_limits = extrusion.limits
                break

            score = _layer_in_mask_score(layer, extrusion.mask_spec)
            if score is not None and score < best_score:
                conductor_limits = extrusion.limits
                best_score = score

        if conductor_limits is None:
            raise RuntimeError(
                f"Unable to find a conductor extrusion specification for layer {layer}. Please "
                f"specify 'conductor_limits' manually."
            )

    z_center = 0.5 * (conductor_limits[0] + conductor_limits[1])
    z_thickness = abs(conductor_limits[1] - conductor_limits[0])
    cpw_min = min(signal_width, gap, z_thickness)

    # Scale found manually by testing a range of configurations
    cpw_scale = gap**0.3 * signal_width**0.6
    ground_factor = 10
    z_factor = 12

    if ground_width is None:
        ground_width = ground_factor * cpw_scale

    offset = (signal_width + ground_width) / 2 + gap
    full_width = signal_width + 2 * gap + 2 * ground_width

    if description is None:
        description = f"CPW (signal width: {signal_width}, gap: {gap})"

    if width is None:
        width = min(full_width, signal_width + 2 * (gap + ground_factor * cpw_scale)) - cpw_min
    elif width >= full_width:
        warnings.warn(
            "CPW width is larger than the ground conductor extension. Please increase "
            "'ground_width' or decrease 'width', otherwise check the port modes to "
            "make sure the mode solver finds the correct modes.",
            stacklevel=2,
        )

    if limits is None:
        z_margin = z_thickness / 2 + z_factor * cpw_scale
        limits = (z_center - z_margin, z_center + z_margin)

    path_profiles = {"signal": (signal_width, 0, layer)}
    if include_ground:
        path_profiles["gnd0"] = (ground_width, -offset, layer)
        path_profiles["gnd1"] = (ground_width, offset, layer)
    if gap_layer is not None:
        gap_offset = (signal_width + gap) / 2
        path_profiles["gap0"] = (gap, -gap_offset, gap_layer)
        path_profiles["gap1"] = (gap, gap_offset, gap_layer)

    return PortSpec(
        description=description,
        width=width,
        limits=limits,
        num_modes=num_modes,
        added_solver_modes=added_solver_modes,
        target_neff=target_neff,
        path_profiles=path_profiles,
        voltage_path=[(signal_width / 2 + gap, z_center), (signal_width / 2, z_center)],
        current_path=Rectangle(center=(0, z_center), size=(signal_width + gap, z_thickness + gap)),
    )


def grid_layout(
    objects: Sequence[Component | Reference | Circle | Path | Polygon | Rectangle],
    gap: float | Sequence[float] = 0,
    shape: Sequence[int] | None = None,
    align_x: Literal["left", "right", "center", "origin"] | None = "center",
    align_y: Literal["bottom", "top", "center", "origin"] | None = "center",
    direction: Literal[
        "lr-bt", "lr-tb", "rl-bt", "rl-tb", "bt-lr", "tb-lr", "bt-rl", "tb-rl"
    ] = "lr-bt",
    include_ports: bool = True,
    layer: tuple[int] = (0, 0),
    name: str | None = None,
) -> Component:
    """
    Arrange components or other structures in a grid layout.

    Args:
        objects: Sequence of objects to arrange. They can be instances of
          :class:`Component`, :class:`Reference`, or 2D structures.
        gap: Horizontal and vertical gaps added between objects.
        shape: Grid shape, specified as ``(columns, rows)``.
        align_x: Horizontal alignment within the grid cell.
        align_y: Vertical alignment within the grid cell.
        direction: Placement order in the grid. Must be a combination of
          ``"lr"`` (left-to-right) or ``"rl"`` (right-to-left), and
          ``"bt"`` (bottom-to-top) or ``"tb"`` (top-to-bottom), as in
          ``"lr-bt"``, ``"rl-tb"``, ``"tb-lr"``, etc.
        include_ports: Whether or not to include ports when computing
          component bounds.
        layer: If arraging geometrical structures, add them to this layer.
        name: Name of the resulting component.

    Returns:
        Component with the objects arranged in a grid.
    """
    num_objects = len(objects)
    if num_objects == 0:
        raise RuntimeError("List of objects cannot be empty.")

    directions = {"rl-bt", "rl-tb", "lr-bt", "lr-tb", "bt-rl", "tb-rl", "bt-lr", "tb-lr"}
    if direction not in directions:
        alternatives = ", ".join(repr(d) for d in sorted(directions))
        raise ValueError(f"Invalid value for 'direction'. Must be one of {alternatives}")

    rows = int(num_objects**0.5 + 0.5) if shape is None else shape[1]
    cols = (num_objects + rows - 1) // rows if shape is None else shape[0]

    if num_objects > rows * cols:
        raise ValueError("More components than available grid slots.")

    if name is None:
        name = f"GRID_{cols}_{rows}"

    bounds = np.array(
        [
            obj.bounds(include_ports) if isinstance(obj, Component) else obj.bounds()
            for obj in objects
        ]
    )

    size = (bounds[:, 1, :] - bounds[:, 0, :]).max(axis=0)
    if align_x == "origin":
        size[0] = bounds[:, 1, 0].max() - bounds[:, 0, 0].min()
    if align_y == "origin":
        size[1] = bounds[:, 1, 1].max() - bounds[:, 0, 1].min()
    size += gap

    x_offsets = [col * size[0] for col in range(cols)]
    y_offsets = [row * size[1] for row in range(rows)]

    if direction[:2] == "rl" or direction[3:] == "rl":
        x_offsets.reverse()
    if direction[:2] == "tb" or direction[3:] == "tb":
        y_offsets.reverse()

    if "r" in direction[:2]:
        offsets = ((x, y) for y in y_offsets for x in x_offsets)
    else:
        offsets = ((x, y) for x in x_offsets for y in y_offsets)
    offsets = np.array(tuple(offsets)[:num_objects])

    if align_x == "left":
        offsets[:, 0] -= bounds[:, 0, 0]
    elif align_x == "right":
        offsets[:, 0] -= bounds[:, 1, 0]
    elif align_x == "center":
        offsets[:, 0] -= bounds[:, :, 0].sum(axis=1) / 2

    if align_y == "bottom":
        offsets[:, 1] -= bounds[:, 0, 1]
    elif align_y == "top":
        offsets[:, 1] -= bounds[:, 1, 1]
    elif align_y == "center":
        offsets[:, 1] -= bounds[:, :, 1].sum(axis=1) / 2

    technology = None
    for i in range(len(objects)):
        if isinstance(objects[i], Component):
            objects[i] = Reference(objects[i])
        if technology is None and isinstance(objects[i], Reference):
            technology = objects[i].component.technology
        objects[i].translate(offsets[i])

    c = Component(name, technology)
    c.add(layer, *objects)
    return c


def pack_layout(
    objects: Sequence[Component | Reference | Circle | Path | Polygon | Rectangle],
    gap: float | Sequence[float] = 0,
    max_size: Sequence[float] = (0, 0),
    aspect_ratio: float = 0,
    grow_factor: float = 1.1,
    sorting: Literal["best", "area"] | None = "best",
    allow_rotation: bool = False,
    method: Literal["bl", "blsf", "bssf", "baf", "cp"] = "blsf",
    include_ports: bool = True,
    layer: tuple[int] = (0, 0),
    name: str = "PACK_{i}",
) -> list[Component]:
    """
    Arrange components or other structures in a grid layout.

    Args:
        objects: Sequence of objects to arrange. They can be instances of
          :class:`Component`, :class:`Reference`, or 2D structures.
        gap: Horizontal and vertical gaps added between objects.
        max_size: Maximal size of the packed component. If not all objects
          fit in a single pack, multiple are used.
        aspect_ratio: Desired width:height ratio for the pack.
        grow_factor: Controls pack size increment. Values closer to 1 can
          result in tighter packs at the cost of more computation.
        sorting: Sorting option for the list of objects. If ``None``,
          objects are packed in the order they are listed; ``'area'`` will
          pack from largest to smallest, and ``"best"`` will try to choose
          the best object to pack at each iteration.
        allow_rotation: If ``True``, objects may be rotated by 90°.
        method: Heuristic used to select a free slot during packing. See
          below for information about the options.
        include_ports: Whether or not to include ports when computing
          component bounds.
        layer: If arranging geometrical structures, add them to this layer.
        name: Name template for the resulting components. Variable ``i`` is
          used to indicate the pack index in the case of multiple packs.

    Returns:
        List of components with the packed objects.

    Note:
        The available methods for selecting a free slot for packing are:

        Bottom left rule (``"bl"``):
          Use the left-most position among the lowest upper y-value options.

        Best long side fit (``"blsf"``):
          Use the position that minimizes the leftover length on the long
          side.

        Best short side fit (``"bssf"``):
          Use the position that minimizes the leftover length on the short
          side.

        Best area fit (``"baf"``):
          Use the smallest available area that fits.

        Contact point rule (``"cp"``):
          Use the position that maximizes the length of the perimeter that
          touches other objects.

    Reference: Jukka Jylänki, *A Thousand Ways to Pack the Bin – A Practical
    Approach to Two-Dimensional Rectangle Bin Packing*, 2010.
    """
    if len(objects) == 0:
        raise RuntimeError("List of objects cannot be empty.")

    technology = None
    for i in range(len(objects)):
        if isinstance(objects[i], Component):
            technology = objects[i].technology
            break
        if isinstance(objects[i], Reference):
            technology = objects[i].component.technology
            break

    bounds = np.array(
        [
            obj.bounds(include_ports) if isinstance(obj, Component) else obj.bounds()
            for obj in objects
        ]
    )
    sizes = bounds[:, 1, :] - bounds[:, 0, :] + gap

    keep_order = sorting != "best"
    if sorting == "area":
        order = sorted(((a * b, i) for i, (a, b) in enumerate(sizes)), reverse=True)
        objects = [objects[i] for _, i in order]
        sizes = [sizes[i] for _, i in order]
    else:
        objects = list(objects)
        sizes = list(sizes)

    for i in range(2):
        if max_size[i] > 0 and any(size[i] > max_size[i] for size in sizes):
            for j in range(len(objects)):
                if sizes[j][i] > max_size[i]:
                    raise RuntimeError(
                        f"{('Width', 'Height')[i]} of 'objects[{j}]' (plus gap) is larger than "
                        f"'max_size[{i}]' ({sizes[j][i]} > {max_size[i]})."
                    )

    packs = []
    while len(objects) > 0:
        pack = _pack_rectangles(
            sizes, method, max_size, aspect_ratio, grow_factor, keep_order, allow_rotation
        )
        if len(pack) == 0:
            raise RuntimeError("Unable to pack objects.")

        packed_objects = []
        for index, corner, rotate in pack:
            obj = objects[index]
            objects[index] = None
            sizes[index] = None
            if isinstance(obj, Component):
                obj = Reference(obj)
            if rotate:
                obj.rotate(90)
            xy_min, _ = obj.bounds()
            obj.translate(corner - xy_min)
            packed_objects.append(obj)

        c = Component(name.format(i=len(packs)), technology)
        c.add(layer, *packed_objects)
        packs.append(c)

        objects = [obj for obj in objects if obj is not None]
        sizes = [size for size in sizes if size is not None]

    return packs
