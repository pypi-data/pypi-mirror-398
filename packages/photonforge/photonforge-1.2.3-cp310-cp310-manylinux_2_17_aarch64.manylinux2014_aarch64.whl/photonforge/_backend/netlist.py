import logging
import math
import pathlib
from multiprocessing import current_process
from uuid import uuid4

import photonforge as pf
from photonforge._backend.component import component_to_node, parse_component
from photonforge._backend.parametric_schema import make_serializable
from photonforge._backend.types import CanvasProperties, Netlist

SCHEMATIC_SCALE_FACTOR = 20.0


logger = logging.getLogger(f"photonforge.server.worker.{current_process().name}.netlist")


def detect_route(component, netlist, route_index, reference):
    fn_name = reference.component.parametric_function
    if fn_name not in ("photonforge.parametric.route", "photonforge.parametric.route_s_bend"):
        return None

    matches = [
        (connection_index, instance_index, port_name)
        for connection_index, connection in enumerate(netlist["connections"])
        for (instance_index, port_name, _), (other_index, _, _) in [
            connection,
            (connection[1], connection[0]),
        ]
        if other_index == route_index
    ]
    if len(matches) == 2:
        # Match connection ports to kwargs ports for ordering
        kwargs_ports = [
            reference.component.parametric_kwargs.get("port1"),
            reference.component.parametric_kwargs.get("port2"),
        ]
        for i in range(2):
            port = kwargs_ports[i]
            if not (port is None or isinstance(port, pf.Port)):
                if len(port) > 1 and isinstance(port[0], pf.Reference):
                    index = port[2] if len(port) > 2 else 0
                    port_list = port[0].get_ports(port[1])
                    kwargs_ports[i] = port_list[index]
                else:
                    kwargs_ports[i] = None

        route_ports = (
            component.references[matches[0][1]][matches[0][2]],
            component.references[matches[1][1]][matches[1][2]],
        )

        if route_ports[0] == kwargs_ports[1] or route_ports[1] == kwargs_ports[0]:
            matches = [matches[1], matches[0]]
        elif route_ports[0] != kwargs_ports[0] and route_ports[1] != kwargs_ports[1]:
            return None

        (connection_index0, instance0, port0), (connection_index1, instance1, port1) = matches

        # TODO: We cannot pass a class to make_serializable without inspecting the
        # original parametric function. We need to create a function that generates
        # these kwargs based on the original function using:
        # fn ~= registry.get(reference.component.parametric_function)
        # schema, info = inspect_parameters(fn, reference.component.parametric_kwargs)
        # ... extract properly serialized defaults
        kwargs = {
            k: make_serializable(v)
            for k, v in reference.component.parametric_kwargs.items()
            if v is not None and k != "port1" and k != "port2"
        }

        fn = getattr(pf.parametric, fn_name[fn_name.rfind(".") + 1 :])
        ref0 = component.references[instance0]
        ref1 = component.references[instance1]

        route = fn(port1=(ref0, port0), port2=(ref1, port1), **kwargs)
        route.name = reference.component.name
        if route != reference.component:
            return None

        netlist["connections"].pop(max(connection_index0, connection_index1))
        netlist["connections"].pop(min(connection_index0, connection_index1))

        # return {
        #     "port1": {"reference": instance0, "port": port0},
        #     "port2": {"reference": instance1, "port": port1},
        #     "function": fn_name,
        #     "kwargs": kwargs,
        # }

        return {
            "id": uuid4(),
            "from": {"nodeId": ref0.component._id, "portId": ref0.component.ports[port0]._id},
            "to": {"nodeId": ref1.component._id, "portId": ref1.component.ports[port1]._id},
            "properties": None,
        }


def component_to_netlist(component: pf.Component) -> Netlist:
    netlist = component.get_netlist()
    if len(component.references) != len(netlist["instances"]):
        raise RuntimeError(
            f"Component '{component.name}' contains array references, which are not supported."
        )

    node_id = {}
    references = []
    routes = []
    for index, reference in enumerate(component.references):
        if reference.columns != 1 or reference.rows != 1:
            raise RuntimeError("Reference array are not supported in netlists")

        route = None  # detect_route(component, netlist, index, reference)

        if route is None:
            # node_id[index] = reference._id
            node_id[index] = reference.component._id
            node = component_to_node(reference.component)
            node.canvasProperties = CanvasProperties(
                position=reference.center() * SCHEMATIC_SCALE_FACTOR,
                rotation=reference.rotation / 180 * math.pi,
                flip=reference.x_reflection,
                zOrder=0,
            )
            references.append(node)
        else:
            routes.append(route)

    connections = [
        {
            "id": uuid4(),
            "from": {"nodeId": node_id[i[0]], "portName": i[1]},
            "to": {"nodeId": node_id[j[0]], "portName": j[1]},
            "properties": None,
        }
        for i, j in netlist["connections"]
    ]

    virtual_connections = [
        {
            "id": uuid4(),
            "from": {"nodeId": node_id[i[0]], "portName": i[1]},
            "to": {"nodeId": node_id[j[0]], "portName": j[1]},
            "properties": None,
        }
        for i, j in netlist["virtual connections"]
    ]

    ports = [
        {"nodeId": node_id[i[0]], "portName": i[1], "externalName": name}
        for i, name in netlist["ports"].items()
    ]

    terminals = [
        {
            "nodeId": node_id[i[0]],
            "portName": i[1][0],
            "terminalName": i[1][1],
            "externalName": name,
        }
        if isinstance(i[1], tuple)
        else {"nodeId": node_id[i[0]], "terminalName": i[1], "externalName": name}
        for i, name in netlist["terminals"].items()
    ]

    result = {
        "nodes": references,
        "virtualConnections": routes + connections + virtual_connections,
        "ports": ports,
        "terminals": terminals,
    }
    return Netlist.model_validate(result)


def netlist_to_component(netlist: Netlist) -> pf.Component:
    references = [parse_component(n) for n in netlist.nodes]

    # We don't know the positions of references, but need to avoid any physical connection
    pf.grid_layout(references, gap=1)

    pf_net = {
        "name": "Netlist Circuit",
        "instances": {r._id: r for r in references},
        "virtual_connections": [
            [(str(c.frm.nodeId), c.frm.portName), (str(c.to.nodeId), c.to.portName)]
            for c in netlist.virtualConnections
        ],
        "ports": [(str(p.nodeId), p.portName, p.externalName) for p in netlist.ports],
        "terminals": [
            (str(t.nodeId), t.terminalName, t.externalName)
            if t.portName is None
            else (str(t.nodeId), (t.portName, t.terminalName), t.externalName)
            for t in netlist.terminals
        ],
        "models": [(pf.CircuitModel(), "Circuit")],
    }

    logger.debug(f"Converting netlist: {pf_net}")

    component = pf.component_from_netlist(pf_net)

    if len(component.ports) == 0:
        logger.warning("Netlist contains no ports: autodetecting")
        component.add_reference_ports()

    return component


if __name__ == "__main__":
    import json
    import pathlib

    from photonforge._backend import fallback_defaults

    path = pathlib.Path(__file__).parent / "../../example_schemas/netlist"
    path.mkdir(exist_ok=True, parents=True)
    for file in path.glob("*.json"):
        file.unlink()

    fallback_defaults()

    component = pf.component_from_netlist(
        {
            "name": "example",
            "instances": [
                pf.parametric.bend(port_spec="Strip", radius=2),
                pf.parametric.straight(port_spec="Strip", length=2),
                {"component": pf.parametric.bend(port_spec="Strip", radius=3), "origin": (20, 50)},
                {"component": pf.parametric.bend(port_spec="Strip", radius=2), "origin": (20, -50)},
                {
                    "component": pf.parametric.straight(port_spec="CPW", length=40),
                    "origin": (-20, 0),
                },
            ],
            "connections": [((0, "P1"), (1, "P0"))],
            "virtual connections": [((1, "P1"), (2, "P0"))],
            "routes": [((2, "P1"), (3, "P0"), {"radius": 3})],
            "ports": [(0, "P0", "IN"), (3, "P1", "OUT"), (4, "E0"), (4, "E1")],
            "terminals": [(4, ("E0", "signal")), (4, ("E1", "signal"))],
            "models": [(pf.CircuitModel(), "Circuit")],
        }
    )

    print(f"Exporting netlist from '{component.name}'…", flush=True)
    netlist = component_to_netlist(component)
    json_data = netlist.model_dump(mode="json")
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
    (path / f"{component.name}.json").write_text(json_str)
