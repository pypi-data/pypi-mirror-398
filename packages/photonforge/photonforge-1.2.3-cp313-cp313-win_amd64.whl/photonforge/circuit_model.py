import struct
import threading
import time
from collections.abc import Sequence
from typing import Any

import numpy

from . import typing as pft
from .cache import _mode_overlap_cache, cache_s_matrix
from .circuit_base import _gather_status, _process_component_netlist
from .extension import (
    Component,
    Model,
    Port,
    SMatrix,
    _connect_s_matrices,
    register_model_class,
)
from .tidy3d_model import _align_and_overlap


class _CircuitModelRunner:
    def __init__(
        self,
        runners: dict[Any, Any],
        frequencies: Sequence[float],
        component_name: str,
        ports: dict[str, Port],
        port_connections: dict[str, tuple[int, str, int]],
        connections: Sequence[tuple[tuple[int, str, int], tuple[int, str, int]]],
        instance_port_data: Sequence[tuple[Any, Any]],
        cost_estimation: bool,
    ) -> None:
        self.runners = runners
        self.frequencies = frequencies
        self.component_name = component_name
        self.ports = ports
        self.port_connections = port_connections
        self.connections = connections
        self.instance_port_data = instance_port_data
        self.cost_estimation = cost_estimation

        self.lock = threading.Lock()
        self._s_matrix = None
        self._status = {"progress": 0, "message": "running", "tasks": {}}

        self.thread = threading.Thread(daemon=True, target=self._run_and_monitor_task)
        self.thread.start()

    def _run_and_monitor_task(self):
        task_status = _gather_status(*self.runners.values())
        w_tasks = 3 * len(task_status["tasks"])
        n_ports = len(self.instance_port_data)
        n_connections = len(self.connections)
        denominator = w_tasks + n_ports + n_connections

        with self.lock:
            self._status = dict(task_status)
            self._status["progress"] *= w_tasks / denominator

        while task_status["message"] == "running":
            time.sleep(0.3)
            task_status = _gather_status(*self.runners.values())
            with self.lock:
                self._status = dict(task_status)
                self._status["progress"] *= w_tasks / denominator

        if task_status["message"] == "error":
            with self.lock:
                self._status = task_status
            return

        with self.lock:
            self._status = task_status
            if self.cost_estimation:
                return
            self._status["message"] = "running"
            self._status["progress"] *= w_tasks / denominator

        s_dict = {}
        for index, (instance_ports, instance_keys) in enumerate(self.instance_port_data):
            # Check if reference is needed
            if instance_ports is None:
                continue

            runner = self.runners[index]
            s_matrix = runner if isinstance(runner, SMatrix) else runner.s_matrix
            if s_matrix is None:
                with self.lock:
                    self._status["message"] = "error"
                return

            # Fix port phases if a rotation is applied
            mode_factor = {
                f"{port_name}@{mode}": 1.0
                for port_name, port in instance_ports
                for mode in range(port.num_modes)
            }

            if instance_keys is not None:
                for port_name, port in instance_ports:
                    key = instance_keys.get(port_name)
                    if key is None:
                        continue

                    # Port mode
                    overlap = _mode_overlap_cache[key]
                    if overlap is None:
                        overlap = _align_and_overlap(
                            self.runners[(index, port_name, 0)].data,
                            self.runners[(index, port_name, 1)].data,
                        )[0]
                        _mode_overlap_cache[key] = overlap

                    for mode in range(port.num_modes):
                        mode_factor[f"{port_name}@{mode}"] = overlap[mode]

            for (i, j), s_ji in s_matrix.elements.items():
                s_dict[(index, i), (index, j)] = s_ji * mode_factor[i] / mode_factor[j]

            with self.lock:
                self._status["progress"] = 100 * (w_tasks + index + 1) / denominator

        s_dict = _connect_s_matrices(s_dict, self.connections, len(self.instance_port_data))

        # Build S matrix with desired ports
        ports = {
            (index, f"{ref_name}@{n}"): f"{port_name}@{n}"
            for (index, ref_name, modes), port_name in self.port_connections.items()
            for n in range(modes)
        }

        elements = {
            (ports[i], ports[j]): s_ji
            for (i, j), s_ji in s_dict.items()
            if i in ports and j in ports
        }

        with self.lock:
            self._s_matrix = SMatrix(self.frequencies, elements, self.ports)
            self._status["progress"] = 100
            self._status["message"] = "success"

    @property
    def status(self) -> dict[str, Any]:
        with self.lock:
            return self._status

    @property
    def s_matrix(self) -> SMatrix:
        with self.lock:
            return self._s_matrix


class CircuitModel(Model):
    """Model based on circuit-level S-parameter calculation.

    The component is expected to be composed of interconnected references.
    Scattering parameters are computed based on the S matrices from all
    references and their interconnections.

    The S matrix of each reference is calculated based on the active model
    of the reference's component. Each calculation is preceded by an update
    to the componoent's technology, the component itself, and its active
    model by calling :attr:`Reference.update`. They are reset to their
    original state after the :func:`CircuitModel.start` function is called.
    Keyword arguents in :attr:`Reference.s_matrix_kwargs` will be passed on
    to :func:`CircuitModel.start`.

    If a reference includes repetitions, it is flattened so that each
    instance is called separatelly.

    Args:
        mesh_refinement: Minimal number of mesh elements per wavelength used
          for mode solving.
        verbose: Flag setting the verbosity of mode solver runs.

    See also:
        `Circuit Model guide <../guides/Circuit_Model.ipynb>`__
    """

    def __init__(
        self,
        mesh_refinement: pft.PositiveFloat | None = None,
        verbose: bool = True,
    ):
        super().__init__(mesh_refinement=mesh_refinement, verbose=verbose)

    @property
    def mesh_refinement(self):
        return self.parametric_kwargs["mesh_refinement"]

    @mesh_refinement.setter
    def mesh_refinement(self, value):
        self.parametric_kwargs["mesh_refinement"] = value

    @property
    def verbose(self):
        return self.parametric_kwargs["verbose"]

    @verbose.setter
    def verbose(self, value):
        self.parametric_kwargs["verbose"] = value

    @cache_s_matrix
    def start(
        self,
        component: Component,
        frequencies: Sequence[float],
        updates: dict[Sequence[str | int | None], dict[str, dict[str, Any]]] = {},
        chain_technology_updates: bool = True,
        verbose: bool | None = None,
        cost_estimation: bool = False,
        **kwargs: Any,
    ) -> _CircuitModelRunner:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            updates: Dictionary of parameter updates to be applied to
              components, technologies, and models for references within the
              main component. See below for further information.
            chain_technology_updates: if set, a technology update will trigger
              an update for all components using that technology.
            verbose: If set, overrides the model's ``verbose`` attribute and
              is passed to reference models.
            cost_estimation: If set, Tidy3D simulations are uploaded, but not
              executed. S matrix will *not* be computed.
            **kwargs: Keyword arguments passed to reference models.

        Returns:
            Result object with attributes ``status`` and ``s_matrix``.

        The ``'updates'`` dictionary contains keyword arguments for the
        :func:`Reference.update` function for the references in the component
        dependency tree, such that, when the S parameter of a specific reference
        are computed, that reference can be updated without affecting others
        using the same component.

        Each key in the dictionary is used as a reference specification. It must
        be a tuple with any number of the following:

        - ``name: str | re.Pattern``: selects any reference whose component name
          matches the given regex.

        - ``i: int``, directly following ``name``: limits the selection to
          ``reference[i]`` from the list of references matching the name. A
          negative value will match all list items. Note that each repetiton in
          a reference array counts as a single element in the list.

        - ``None``: matches any reference at any depth.

        Examples:
            >>> updates = {
            ...     # Apply component updates to the first "ARM" reference in
            ...     # the main component
            ...     ("ARM", 0): {"component_updates": {"radius": 10}}
            ...     # Apply model updates to the second "BEND" reference under
            ...     # any "SUB" references in the main component
            ...     ("SUB", "BEND", 1): {"model_updates": {"verbose": False}}
            ...     # Apply technology updates to references with component name
            ...     # starting with "COMP_" prefix, at any subcomponent depth
            ...     (None, "COMP.*"): {"technology_updates": {"thickness": 0.3}}
            ... }
            >>> s_matrix = component.s_matrix(
            ...     frequencies, model_kwargs={"updates": updates}
            ... )

        See also:
            - `Circuit Model guide <../guides/Circuit_Model.ipynb>`__
            - `Cascaded Rings Filter example
              <../examples/Cascaded_Rings_Filter.ipynb>`__
        """
        if verbose is None:
            verbose = self.verbose
            s_matrix_kwargs = {}
        else:
            s_matrix_kwargs = {"verbose": verbose}
        if cost_estimation:
            s_matrix_kwargs["cost_estimation"] = cost_estimation

        frequencies = numpy.array(frequencies, dtype=float, ndmin=1)
        runners, _, component_ports, port_connections, connections, instance_port_data, _ = (
            _process_component_netlist(
                component,
                frequencies,
                self.mesh_refinement,
                {},
                updates,
                chain_technology_updates,
                verbose,
                cost_estimation,
                kwargs,
                s_matrix_kwargs,
                None,
            )
        )

        return _CircuitModelRunner(
            runners,
            frequencies,
            component.name,
            component_ports,
            port_connections,
            connections,
            instance_port_data,
            cost_estimation,
        )

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "CircuitModel":
        """De-serialize this model."""
        (version, verbose, mesh_refinement) = struct.unpack("<B?d", byte_repr)
        if version != 0:
            raise RuntimeError("Unsuported CircuitModel version.")

        if mesh_refinement <= 0:
            mesh_refinement = None
        return cls(mesh_refinement, verbose)


register_model_class(CircuitModel)
