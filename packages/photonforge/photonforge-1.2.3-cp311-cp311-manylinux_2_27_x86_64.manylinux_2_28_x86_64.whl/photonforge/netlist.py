from itertools import chain
from typing import Any

from .extension import Component, Reference
from .parametric import route, route_manhattan


def component_from_netlist(netlist: dict[str, Any]) -> Component:
    """Create a component from a netlist description.

    Args:
        netlist: Dictionary with the component description. The only
          required key is ``'instances'``, which describes the references to
          all sub-components. See other keys in the example below.

    Examples:
        >>> coupler = parametric.dual_ring_coupler(
        ...     port_spec="Strip",
        ...     coupling_distance=0.6,
        ...     radius=4,
        ... )
        ... bus = parametric.ring_coupler(
        ...     port_spec="Strip",
        ...     coupling_distance=0.6,
        ...     radius=4,
        ...     bus_length=5,
        ... )
        >>> netlist1 = {
        ...     "name": "RING",
        ...     "instances": {"COUPLER": coupler, "BUS_0": bus, "BUS_1": bus},
        ...     "instance models": [
        ...         ("COUPLER", DirectionalCouplerModel(0.8, -0.5j)),
        ...     ],
        ...     "connections": [
        ...         (("COUPLER", "P0"), ("BUS_0", "P1")),
        ...         (("BUS_1", "P1"), ("COUPLER", "P3")),
        ...     ],
        ...     "ports": [
        ...         ("BUS_0", "P0"),
        ...         ("BUS_0", "P2"),
        ...         ("BUS_1", "P2"),
        ...         ("BUS_1", "P0"),
        ...     ],
        ...     "models": [CircuitModel()],
        ... }
        >>> component1 = component_from_netlist(netlist1)

        >>> netlist2 = {
        ...     "instances": [
        ...         coupler,
        ...         {"component": bus, "origin": (0, -12)},
        ...         {"component": bus, "origin": (3, 7), "rotation": 180},
        ...     ],
        ...     "virtual connections": [
        ...         ((0, "P0"), (1, "P1")),
        ...         ((0, "P2"), (1, "P3")),
        ...         ((2, "P3"), (0, "P1")),
        ...     ],
        ...     "routes": [
        ...         ((1, "P2"), (2, "P0"), {"radius": 6}),
        ...         ((2, "P1"), (0, "P3"), parametric.route_s_bend),
        ...     ],
        ...     "ports": [
        ...         (1, "P0", "In"),
        ...         (2, "P2", "Add"),
        ...     ],
        ...     "models": [(CircuitModel(), "Circuit")],
        ...     "active models": {"optical": "Circuit"},
        ... }
        >>> component2 = component_from_netlist(netlist2)

        >>> spec = cpw_spec("METAL", 3, 1)
        ... tl = parametric.straight(port_spec=spec, length=20)
        ... terminal = Terminal(
        ...     "METAL", Rectangle(center=(-10, 20), size=(2, 2))
        ... )
        ... tl.add_terminal(terminal, "T0")
        ... netlist3 = {
        ...     "instances": [tl],
        ...     "terminal routes": [
        ...         ((0, "T0"), (0, ("E0", "gnd0"))),
        ...     ],
        ...     "terminals": [
        ...         (0, "T0", "GND0"),
        ...         (0, ("E1", "gnd0"), "GND1"),
        ...     ],
        ... }
        >>> component3 = component_from_netlist(netlist3)

    The value in ``"instances"`` can be a dictionary or a list, in which
    case, index numbers are used in place of the keys. Each value can be a
    :class:`Component`, a :class:`Reference`, or a dictionary with keyword
    arguments to create a :class:`Reference`.

    Sub-components can receive extra models from ``"instance models"``. The
    last added model for each sub-component will be active.

    The ``"connections"`` list specifies connections between instances. Each
    item is of the form ``((key1, port1), (key2, port2))``, indicating that
    the reference ``key1`` must be transformed to have its ``port1``
    connected to ``port2`` from the reference ``key2``.

    Items in the ``"routes"`` list contain 2 reference ports, similarly to
    ``"connections"``, plus an optional routing function and a dictionary of
    keyword arguments to the function:
    ``((key1, port1), (key2, port2), route_function, kwargs_dict)``. If
    ``route_function`` is not provided, :func:`photonforge.parametric.route`
    is used.

    A list of ``"terminal routes"`` can be also be specified analogously to
    ``"routes"``, with the difference that only terminal routing functions
    can be used and :func:`photonforge.parametric.route_manhattan` is the
    default. Terminals within ports can also be used by replacing the
    terminal name string with a tuple ``(port_name, terminal_name)``.

    The ``"ports"`` list specify the top-level component ports derived from
    instance ports from ``(key, port)`` or ``(key, port, new_name)``. The
    same goes for the ``"terminals"`` lists, except that terminal names can
    be replaced by a ``(port_name, terminal_name)`` tuple to indicate a
    terminals within a port.
    """
    component = Component(netlist.get("name", ""))

    references = {}
    instances = netlist["instances"]
    instances_items = instances.items() if isinstance(instances, dict) else enumerate(instances)
    for key, instance in instances_items:
        reference = (
            Reference(**instance)
            if isinstance(instance, dict)
            else (instance if isinstance(instance, Reference) else Reference(instance))
        )
        component.add(reference)
        references[key] = reference

    # Order matters here
    for connection in netlist.get("connections", ()):
        key1, port1 = connection[0]
        key2, port2 = connection[1]
        references[key1].connect(port1, references[key2][port2])

    for connection in chain(
        netlist.get("virtual connections", ()), netlist.get("virtual_connections", ())
    ):
        key1, port1 = connection[0]
        key2, port2 = connection[1]
        component.add_virtual_connection(references[key1], port1, references[key2], port2)

    for connection in netlist.get("routes", ()):
        key1, port1 = connection[0]
        key2, port2 = connection[1]
        route_fn = connection[2] if len(connection) > 2 and callable(connection[2]) else route
        kwargs = connection[-1] if isinstance(connection[-1], dict) else {}
        component.add(
            route_fn(port1=references[key1][port1], port2=references[key2][port2], **kwargs)
        )

    for connection in chain(netlist.get("terminal routes", ()), netlist.get("terminal_routes", ())):
        terminals = [
            references[key][terminal]
            if isinstance(terminal, str)
            else references[key][terminal[0]].terminals(terminal[1])
            for key, terminal in connection[:2]
        ]
        if terminals[0] is None or terminals[1] is None:
            i = 0 if terminals[0] is None else 1
            raise RuntimeError(
                f"Terminal specification {connection[i]} from 'terminal routes' does not exist."
            )
        route_fn = (
            connection[2] if len(connection) > 2 and callable(connection[2]) else route_manhattan
        )
        kwargs = connection[-1] if isinstance(connection[-1], dict) else {}
        component.add(route_fn(terminal1=terminals[0], terminal2=terminals[1], **kwargs))

    for item in netlist.get("ports", ()):
        if len(item) == 3:
            key, port, name = item
        else:
            key, port = item
            name = None
        component.add_port(references[key][port], name)

    for item in netlist.get("terminals", ()):
        if len(item) == 3:
            key, terminal, name = item
        else:
            key, terminal = item
            name = None
        terminal = (
            references[key][terminal]
            if isinstance(terminal, str)
            else references[key][terminal[0]].terminals(terminal[1])
        )
        if terminal is None:
            raise RuntimeError(
                f"Terminal specification {item[:2]} from 'terminals' does not exist."
            )
        component.add_terminal(terminal, name)

    for item in netlist.get("models", ()):
        if isinstance(item, tuple):
            model, name = item
        else:
            model = item
            name = None
        component.add_model(model, name)

    for classification, model_name in chain(
        netlist.get("active models", {}).items(), netlist.get("active_models", {}).items()
    ):
        component.activate_model(model_name, classification=classification)

    for item in chain(netlist.get("instance models", ()), netlist.get("instance_models", ())):
        if len(item) == 3:
            key, model, name = item
        else:
            key, model = item
            name = None
        references[key].component.add_model(model, name)

    return component
