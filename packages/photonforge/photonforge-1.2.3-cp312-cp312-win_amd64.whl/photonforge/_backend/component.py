import logging
from multiprocessing import current_process

import numpy as np

import photonforge as pf
from photonforge._backend.parametric_schema import inspect_parameters, kwargs_from_schema
from photonforge._backend.types import ActiveModels, Node, Port, Terminal

logger = logging.getLogger(f"photonforge.server.worker.{current_process().name}.component")


def port_properties(port, xmin, ymin, xmax, ymax):
    c = port.center
    direction = (
        port.input_direction
        if isinstance(port, pf.Port)
        else (np.arctan2(port.input_vector[1], port.input_vector[0]) / np.pi * 180)
    ) % 360
    _, _, side, coord = min(
        (min(0, c[0] - xmin), min(direction, 360 - direction), "left", -c[1].item()),
        (min(0, xmax - c[0]), abs(direction - 180), "right", -c[1].item()),
        (min(0, c[1] - ymin), abs(direction - 90), "bottom", c[0].item()),
        (min(0, ymax - c[1]), abs(direction - 270), "top", c[0].item()),
    )
    return side, coord


def terminal_properties(terminal, xmin, ymin, xmax, ymax):
    c = terminal.center()
    _, _, side, coord = min(
        (min(0, c[0] - xmin), 2, "left", -c[1].item()),
        (min(0, xmax - c[0]), 3, "right", -c[1].item()),
        (min(0, c[1] - ymin), 0, "bottom", c[0].item()),
        (min(0, ymax - c[1]), 1, "top", c[0].item()),
    )
    return side, coord


def set_offsets(items):
    n = len(items)
    if n <= 1:
        g = g0 = 0
    else:
        g = 1 / n
        g0 = -0.5 + g / 2
    items.sort(key=lambda item: (item["canvasProperties"]["offset"], item["name"]))
    for i in range(n):
        items[i]["canvasProperties"]["offset"] = g0 + i * g


def get_ports_and_terminals(component):
    (xmin, ymin), (xmax, ymax) = component.bounds()
    d = min(ymax - ymin, xmax - xmin) / 4
    xmin += d
    ymin += d
    xmax -= d
    ymax -= d
    items_by_side = {"left": [], "right": [], "bottom": [], "top": []}
    for name, port in component.ports.items():
        side, coord = port_properties(port, xmin, ymin, xmax, ymax)
        items_by_side[side].append(
            {
                "id": port._id,
                "name": name,
                "classificationType": port.classification,
                "numModes": port.num_modes,
                "baseType": port.__class__.__name__,
                "canvasProperties": {"side": side, "offset": coord},
            }
        )
        if port.classification == "electrical":
            for term_name, terminal in port.terminals().items():
                side, coord = terminal_properties(terminal, xmin, ymin, xmax, ymax)
                items_by_side[side].append(
                    {
                        "id": terminal._id,
                        "name": term_name,
                        "port": port._id,
                        "canvasProperties": {"side": side, "offset": coord},
                    }
                )
    for name, terminal in component.terminals.items():
        side, coord = terminal_properties(terminal, xmin, ymin, xmax, ymax)
        items_by_side[side].append(
            {
                "id": terminal._id,
                "name": name,
                "port": None,
                "canvasProperties": {"side": side, "offset": coord},
            }
        )
    for items in items_by_side.values():
        set_offsets(items)
    ports = []
    terminals = []
    for items in items_by_side.values():
        for item in items:
            if "port" in item:
                terminals.append(Terminal.model_validate(item))
            else:
                ports.append(Port.model_validate(item))
    return ports, terminals


def component_to_node(component_or_fn) -> Node:
    if isinstance(component_or_fn, pf.Component):
        component = component_or_fn
        kwargs = component.parametric_kwargs
    else:
        component = component_or_fn()
        if not isinstance(component, pf.Component):
            raise TypeError("Expected 'Component' type.")
        kwargs = {}

    # TODO: Replace with online resource URI
    thumbnail = pf.thumbnails[component.properties.get("__thumbnail__")]

    active_models = {}
    for classification in ("electrical", "optical"):
        active = component.select_active_model(classification)
        for name, model in component.models.items():
            if model is active:
                active_models[classification] = name
                break

    models = {
        name: inspect_parameters(model.__class__, model.parametric_kwargs)[0]
        for name, model in component.models.items()
    }

    time_steppers = {
        name: inspect_parameters(
            model.time_stepper.__class__, model.time_stepper.parametric_kwargs
        )[0]
        for name, model in component.models.items()
    }

    ports, terminals = get_ports_and_terminals(component)

    fn = pf._component_registry.get(component.parametric_function)

    return Node(
        id=component._id,
        componentId=component._id,
        name=component.name,
        parameters=inspect_parameters(fn, kwargs)[0] if fn else {},
        modelParameters=models,
        timeStepperParameters=time_steppers,
        activeModel=ActiveModels(**active_models),
        ports=ports,
        terminals=terminals,
        thumbnail=thumbnail,
        preview=component._repr_svg_(),
    )


def parse_component(node: Node) -> pf.Reference:
    from photonforge._backend.worker import from_pda  # noqa: PLC0415

    component = from_pda(node.componentId)
    if component is None or not isinstance(component, pf.Component):
        raise RuntimeError(f"Invalid component ID {node.componentId}.")

    fn = pf._component_registry.get(component.parametric_function)
    if fn is None:
        component_kwargs = {}
    else:
        _, classes = inspect_parameters(fn)
        component_kwargs = kwargs_from_schema(node.parameters, classes)

    model_kwargs = {}
    for model_name, model in component.models.items():
        schema = node.modelParameters.get(model_name)
        if schema is None:
            continue
        _, classes = inspect_parameters(model.__class__)
        model_kwargs[model_name] = kwargs_from_schema(schema, classes)

    reference = pf.Reference(
        component, component_updates=component_kwargs, model_updates=model_kwargs
    )
    reference._id = str(node.id)
    if node.canvasProperties:
        if node.canvasProperties.rotation is not None:
            reference.rotation = node.canvasProperties.rotation / np.pi * 180
        if node.canvasProperties.flip:
            reference.x_reflection = True

    logger.debug(
        f"Created reference {reference._id} to component {component._id} with component updates "
        f"{component_kwargs} and model updates {model_kwargs}"
    )

    return reference


if __name__ == "__main__":
    import json
    import pathlib

    from photonforge._backend import fallback_defaults

    path = pathlib.Path(__file__).parent / "../../example_schemas/component"
    path.mkdir(exist_ok=True, parents=True)
    for file in path.glob("*.json"):
        file.unlink()

    fallback_defaults()
    port_spec = pf.virtual_port_spec(1)
    port_spec2 = pf.virtual_port_spec(2)

    psr6 = pf.PolarizationSplitterRotatorModel().black_box_component(
        port_spec=port_spec2, output_port_spec=port_spec2
    )
    psr6.name = psr6.name + "6"

    psr4 = pf.PolarizationSplitterRotatorModel().black_box_component(
        port_spec=port_spec2, output_port_spec=port_spec
    )
    psr4.name = psr4.name + "4"

    components = [
        getattr(pf.parametric, x)()
        for x in dir(pf.parametric)
        if x[0] != "_" and not x.startswith("route")
    ] + [
        pf.TerminationModel().black_box_component(),
        pf.TwoPortModel().black_box_component(),
        pf.PowerSplitterModel().black_box_component(),
        pf.PolarizationBeamSplitterModel().black_box_component(),
        psr6,
        psr4,
        pf.DirectionalCouplerModel().black_box_component(),
        pf.CrossingModel().black_box_component(),
        pf.AnalyticWaveguideModel(
            n_eff=2.9, reference_frequency=pf.C_0 / 1.55
        ).black_box_component(),
        pf.AnalyticDirectionalCouplerModel(
            interaction_length=5, coupling_length=10
        ).black_box_component(),
    ]

    for component in components:
        if component.parametric_function is None:
            name = component.name
        else:
            name = component.parametric_function[23:]
        print(f"Exporting '{name}'…", flush=True)
        node = component_to_node(component)
        json_data = node.model_dump(mode="json")
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        (path / f"{name}.json").write_text(json_str)
