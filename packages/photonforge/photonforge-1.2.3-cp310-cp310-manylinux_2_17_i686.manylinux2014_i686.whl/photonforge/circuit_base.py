import re
import warnings
from collections.abc import Sequence
from typing import Any, Literal

import numpy
import tidy3d

from .extension import (
    Component,
    GaussianPort,
    Port,
    Reference,
    SMatrix,
    _content_repr,
    frequency_classification,
)
from .tidy3d_model import _ModeSolverRunner


def _gather_status(*runners: Any) -> dict[str, Any]:
    """Create an overall status based on a collection of runners."""
    num_tasks = 0
    progress = 0
    message = "success"
    tasks = {}
    for task in runners:
        task_status = (
            {"progress": 100, "message": "success"} if isinstance(task, SMatrix) else task.status
        )
        inner_tasks = task_status.get("tasks", {})
        tasks.update(inner_tasks)
        task_weight = max(1, len(inner_tasks))
        num_tasks += task_weight
        if message != "error":
            if task_status["message"] == "error":
                message = "error"
            elif task_status["message"] == "running":
                message = "running"
                progress += task_weight * task_status["progress"]
            elif task_status["message"] == "success":
                progress += task_weight * 100
    if message == "running":
        progress /= num_tasks
    else:
        progress = 100
    return {"progress": progress, "message": message, "tasks": tasks}


def _reference_ports(component, level, cache):
    if cache is not None and len(cache) > level:
        return cache[level]
    result = []
    index = 0
    if level == 0:
        for reference in component.references:
            for instance in reference.get_repetition():
                result.extend((index, k, v[0]) for k, v in instance.get_ports().items())
                index += 1
    else:
        for reference in component.references:
            ports = _reference_ports(reference.component, level - 1, None)
            for instance in reference.get_repetition():
                for *x, name, port in ports:
                    instance.component = Component(name="", technology=component.technology)
                    instance.component.add_port(port, name)
                    result.append((index, *x, name, instance[name]))
                index += 1
    if cache is not None:
        cache.append(result)
    return result


def _get_port_by_instance(component, port, cache):
    level = 0
    level_ports = _reference_ports(component, level, cache)
    while len(level_ports) > 0:
        for x in level_ports:
            if x[-1] == port:
                return x
        level += 1
        level_ports = _reference_ports(component, level, cache)
    return None


def _validate_query(
    key: tuple[str | re.Pattern | int | None],
) -> tuple[tuple[re.Pattern, int] | None]:
    if len(key) == 0:
        raise KeyError("Empty key is not allowed as query parameter.")
    valid_key = []
    expect_int = False
    for i, k in enumerate(key):
        if k is None:
            if len(valid_key) == 0 or valid_key[-1] is not None:
                valid_key.append(None)
            expect_int = False
        elif isinstance(k, str):
            valid_key.append((re.compile(k), -1))
            expect_int = True
        elif isinstance(k, re.Pattern):
            valid_key.append((re.compile(k), -1))
            expect_int = True
        elif isinstance(k, int) and expect_int:
            valid_key[-1] = (valid_key[-1][0], k)
            expect_int = False
        elif (
            isinstance(k, tuple)
            and len(k) == 2
            and isinstance(k[0], re.Pattern)
            and isinstance(k[1], int)
        ):
            valid_key.append(k)
        else:
            raise RuntimeError(
                f"Invalid value in position {i} in key {tuple(key)}: {k}. Expected a "
                "string, a compiled regular expression pattern, "
                + ("an integer, " if expect_int else "")
                + "or 'None'."
            )
    return tuple(valid_key)


def _compare_angles(a: float, b: float) -> bool:
    r = (a - b) % 360
    return r <= 1e-12 or 360 - r <= 1e-12


# Return a flattening key (for caching) if flattening is required, and
# a bool indicating whether phase correction is required
def _analyze_transform(
    reference: Reference,
    classification: Literal["optical", "electrical"],
    frequencies: Sequence[float],
) -> tuple[tuple[tuple[float, float] | None, float, bool] | None, bool]:
    technology = reference.component.technology

    background_medium = technology.get_background_medium(classification)
    extrusion_media = [e.get_medium(classification) for e in technology.extrusion_specs]

    uniform = background_medium.is_spatially_uniform and all(
        medium.is_spatially_uniform for medium in extrusion_media
    )

    translated = not numpy.allclose(reference.origin, (0, 0), atol=1e-12)
    rotated = not _compare_angles(reference.rotation, 0)

    if not uniform and (translated or rotated):
        return (tuple(reference.origin.tolist()), reference.rotation, reference.x_reflection), None

    if reference.x_reflection:
        return (None, reference.rotation, reference.x_reflection), None

    # _align_and_overlap only works for rotations that are a multiple of 90°
    rotation_fraction = reference.rotation % 90
    is_multiple_of_90 = rotation_fraction < 1e-12 or (90 - rotation_fraction < 1e-12)
    if not is_multiple_of_90:
        return (None, reference.rotation, reference.x_reflection), None

    # _align_and_overlap does not support angled ports either
    ports = reference.component.select_ports(classification)
    for port in ports.values():
        if isinstance(port, GaussianPort):
            _, _, _, theta, _ = port._axis_aligned_properties(frequencies)
        else:
            _, _, _, theta, _ = port._axis_aligned_properties()
        if theta != 0.0:
            return (None, reference.rotation, reference.x_reflection), None

    translated_mask = any(e.mask_spec.uses_translation() for e in technology.extrusion_specs)
    if translated_mask and rotated:
        return (None, reference.rotation, reference.x_reflection), None

    fully_anisotropic = background_medium.is_fully_anisotropic or any(
        medium.is_fully_anisotropic for medium in extrusion_media
    )
    in_plane_isotropic = (
        not fully_anisotropic
        and (
            not isinstance(background_medium, tidy3d.AnisotropicMedium)
            or background_medium.xx == background_medium.yy
        )
        and all(
            (not isinstance(medium, tidy3d.AnisotropicMedium) or medium.xx == medium.yy)
            for medium in extrusion_media
        )
    )

    if (fully_anisotropic and rotated) or (
        not in_plane_isotropic and rotated and not _compare_angles(reference.rotation, 180)
    ):
        return (None, reference.rotation, reference.x_reflection), None

    return None, rotated


def _process_component_netlist(
    component,
    frequencies,
    mesh_refinement,
    monitors,
    updates,
    chain_technology_updates,
    verbose,
    cost_estimation,
    kwargs,
    s_matrix_kwargs,
    time_stepper_kwargs,
):
    classification = frequency_classification(frequencies)
    netlist = component.get_netlist()

    # 'inputs' is not supported in CircuitModel
    kwargs = dict(kwargs)
    if "inputs" in kwargs:
        del kwargs["inputs"]

    reference_index = {}

    valid_updates = [(_validate_query(k), v) for k, v in updates.items()]

    if isinstance(monitors, dict):
        valid_monitors = []
        cache = []
        for monitor_name, port in monitors.items():
            match = _get_port_by_instance(component, port, cache)
            if match is None:
                warnings.warn(
                    f"{port} does not match any circuit ports and will be ignored.", stacklevel=2
                )
            else:
                *indices, port_name, port = match
                valid_monitors.append((indices, port_name, port.num_modes, monitor_name))
    else:
        valid_monitors = monitors

    # Store copies of instance ports and their reference for phase correction
    instance_port_data = [(None, None)] * len(netlist["instances"])

    runners = {}
    time_steppers = {}
    flattened_component_cache = {}
    active_monitors = []

    for index, reference in enumerate(netlist["instances"]):
        ref_component = reference.component
        current_reference_index = reference_index.get(ref_component.name, -1) + 1
        reference_index[ref_component.name] = current_reference_index

        if ref_component.select_active_model(classification) is None:
            # Check if the model is really needed
            if any(
                index0 == index or index1 == index
                for (index0, _, _), (index1, _, _) in netlist["connections"]
            ) or any(i == index for i, _, _ in netlist["ports"]):
                raise RuntimeError(f"Component '{ref_component.name}' has no active model.")
            continue

        ports = ref_component.select_ports(classification)
        instance_port_data[index] = (
            tuple((port_name, port.copy(True)) for port_name, port in ports.items()),
            None,
        )

        # Match updates with current reference
        reference_updates = {}
        technology_updates = {}
        component_updates = {}
        model_updates = {}
        for key, value in valid_updates:
            if key[0] is None:
                reference_updates[key] = value
                key = key[1:]
            if len(key) == 0:
                technology_updates.update(value.get("technology_updates", {}))
                component_updates.update(value.get("component_updates", {}))
                model_updates.update(value.get("model_updates", {}))
            elif key[0][0].match(ref_component.name):
                if key[0][1] < 0 or key[0][1] == current_reference_index:
                    if len(key) == 1:
                        technology_updates.update(value.get("technology_updates", {}))
                        component_updates.update(value.get("component_updates", {}))
                        model_updates.update(value.get("model_updates", {}))
                    else:
                        reference_updates[key[1:]] = value

        # Match monitors
        monitors = []
        for indices, port_name, num_modes, monitor_name in valid_monitors:
            if indices[0] == index:
                if len(indices) == 1:
                    active_monitors.append((index, port_name, num_modes, monitor_name))
                else:
                    active_monitors.append((index, monitor_name, num_modes, monitor_name))
                    monitors.append((indices[1:], port_name, num_modes, monitor_name))

        # Apply required updates
        reset_list = reference.update(
            technology_updates=technology_updates,
            component_updates=component_updates,
            model_updates=model_updates,
            chain_technology_updates=chain_technology_updates,
            classification=classification,
        )

        # Account for reference transformations
        inner_component = ref_component
        flattening_key, requires_phase_correction = _analyze_transform(
            reference, classification, frequencies
        )
        if flattening_key is not None:
            flattening_key = _content_repr(ref_component, *flattening_key, include_config=False)
            inner_component = flattened_component_cache.get(flattening_key)
            if inner_component is None:
                inner_component = reference.transformed_component(ref_component.name + "-flattened")
                flattened_component_cache[flattening_key] = inner_component
        elif requires_phase_correction:
            # S matrix correction factor depends on the mode solver for transformed ports
            port_keys = {}
            for port_name, port in ports.items():
                # No mode solver runs for 1D ports
                if isinstance(port, Port) and port.spec.limits[1] != port.spec.limits[0]:
                    runners[(index, port_name, 0)] = _ModeSolverRunner(
                        port,
                        frequencies[:1],
                        mesh_refinement,
                        ref_component.technology,
                        cost_estimation=cost_estimation,
                        verbose=verbose,
                    )
                    runners[(index, port_name, 1)] = _ModeSolverRunner(
                        reference[port_name],
                        frequencies[:1],
                        mesh_refinement,
                        ref_component.technology,
                        cost_estimation=cost_estimation,
                        verbose=verbose,
                    )
                    port_keys[port_name] = _content_repr(
                        ref_component.technology,
                        port.spec,
                        port.input_direction % 360,
                        port.inverted,
                        reference.rotation % 360,
                        include_config=False,
                    )

            instance_port_data[index] = (instance_port_data[index][0], port_keys)

        if time_stepper_kwargs is not None:
            instance_kwargs = dict(time_stepper_kwargs)
            instance_kwargs["updates"] = {}
            instance_kwargs["chain_technology_updates"] = chain_technology_updates
            instance_kwargs.update(kwargs)
            instance_kwargs.update(reference_updates.pop("time_stepper_kwargs", {}))
            # TODO: Reference.time_stepper_kwargs
            # if reference.time_stepper_kwargs is not None:
            #     instance_kwargs.update(reference.time_stepper_kwargs)
            instance_kwargs["updates"].update(reference_updates)
            instance_kwargs["monitors"] = monitors
            instance_kwargs["component"] = inner_component
            instance_kwargs["show_progress"] = False

            time_stepper = ref_component.select_active_model(classification).time_stepper.__copy__()
            time_steppers[index] = time_stepper
            runners[index] = time_stepper.setup_state(**instance_kwargs)

        elif s_matrix_kwargs is not None:
            instance_kwargs = dict(s_matrix_kwargs)
            instance_kwargs["updates"] = {}
            instance_kwargs["chain_technology_updates"] = chain_technology_updates
            instance_kwargs.update(kwargs)
            instance_kwargs.update(reference_updates.pop("s_matrix_kwargs", {}))
            if reference.s_matrix_kwargs is not None:
                instance_kwargs.update(reference.s_matrix_kwargs)
            instance_kwargs["updates"].update(reference_updates)

            runners[index] = ref_component.select_active_model(classification).start(
                inner_component, frequencies, **instance_kwargs
            )

        # Reset all updates
        for item, kwds in reset_list:
            item.parametric_kwargs = kwds
            item.update()

    if len(runners) == 0:
        warnings.warn(
            f"No subcomponents found in the circuit model for component '{component.name}'.",
            stacklevel=2,
        )

    component_ports = {
        name: port.copy(True) for name, port in component.select_ports(classification).items()
    }
    port_connections = netlist["ports"]
    # In the circuit model, virtual connections behave like real connections
    connections = netlist["connections"] + netlist["virtual connections"]

    return (
        runners,
        time_steppers,
        component_ports,
        port_connections,
        connections,
        instance_port_data,
        active_monitors,
    )
