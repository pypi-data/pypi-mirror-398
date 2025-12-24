import collections
import io
import json
import pathlib
import struct
import threading
import time
import warnings
import zlib
from collections.abc import Iterable, Sequence
from typing import Any, Literal, Union, get_args

import numpy
import pydantic
import tidy3d
import xarray
from tidy3d.components.data.data_array import DATA_ARRAY_MAP, ScalarModeFieldDataArray
from tidy3d.plugins.mode import ModeSolver

from . import typing as pft
from .cache import _cache_path, _mode_solver_cache, _tidy3d_model_cache, cache_s_matrix
from .extension import (
    Z_MAX,
    Component,
    FiberPort,
    GaussianPort,
    Model,
    Port,
    PortSpec,
    SMatrix,
    Technology,
    _auto_scale_from_refinement,
    _content_repr,
    _from_bytes,
    _layer_steps_from_refinement,
    _local_tidy3d_solver,
    _make_layer_refinement_spec,
    config,
    frequency_classification,
    register_model_class,
    snap_to_grid,
)
from .parametric_utils import _filename_cleanup, _safe_hash
from .utils import C_0

_Tidy3dBaseModel = tidy3d.components.base.Tidy3dBaseModel
_MonitorData = tidy3d.components.data.monitor_data.MonitorData
_ElectromagneticFieldData = tidy3d.components.data.monitor_data.ElectromagneticFieldData

_IsotropicUniformTypes = get_args(tidy3d.components.medium.IsotropicUniformMediumType)

_PerElementMap = pft.annotate(
    Sequence[Sequence[str, str], Sequence[str, str], complex | pft.array(complex, 2)],
    brand="PhotonForgePortSymmetryPerElement",
)
_ExplictMap = pft.annotate(
    Sequence[str, str, dict[str, str]], brand="PhotonForgePortSymmetryExplicit"
)
_ImplicitMap = pft.annotate(Sequence[str | int], brand="PhotonForgePortSymmetryImplicit")

_PortSymmetryType = Sequence[_ExplictMap] | Sequence[_ImplicitMap] | Sequence[_PerElementMap]

_SymmetryType = pft.annotate(Sequence[int], brand="Tidy3dSymmetry")
_SubpixelType = tidy3d.SubpixelSpec | bool
_BoundsType = pft.annotate(Sequence[Sequence[float | None]], brand="PhotonForgeOptionalBounds")
_MonitorType = pft.annotate(tidy3d.components.monitor.MonitorType, brand="Tidy3dMonitor")


# Polling interval for Tidy3D tasks
TIDY3D_POLLING_INTERVAL: float = 1.0

# Overlap threshold to discard modes in symmetry mapping
OVERLAP_THRESHOLD: float = 0.1

use_local_mode_solver: bool = False

_pending_tasks_lock = threading.Lock()
_pending_tasks: set = set()


def abort_pending_tasks() -> list[str]:
    """Abort all known pending Tidy3D pending tasks.

    Returns:
        List of aborted task ids.
    """
    from tidy3d.web.api.webapi import abort  # noqa: PLC0415
    from tidy3d.web.core.exceptions import WebError  # noqa: PLC0415

    if _pending_tasks_lock is None:
        return []

    with _pending_tasks_lock:
        result = list(_pending_tasks)
        while len(_pending_tasks) > 0:
            task_id = _pending_tasks.pop()
            try:
                abort(task_id)
            except WebError:
                pass
    return result


def _tidy3d_to_str(obj: _Tidy3dBaseModel) -> str:
    if (
        isinstance(obj, tidy3d.components.medium.MediumType.__args__)
        and obj.name is not None
        and len(obj.name) > 0
    ):
        return obj.name
    d = obj.dict()
    return (
        f"{obj.__class__.__name__}(" + ", ".join(f"{k}={d[k]!r}" for k in obj.__fields_set__) + ")"
    )


_HDF5_HEADER = b"\x89\x48\x44\x46\x0d\x0a\x1a\x0a"
_JSON = b"\x00\x00"


def _tidy3d_to_bytes(obj: _Tidy3dBaseModel) -> bytes:
    json_str = obj._json()
    if any((key in json_str for key, _ in DATA_ARRAY_MAP.items())):
        buffer = io.BytesIO()
        obj.to_hdf5(buffer)
        result = buffer.getvalue()
    else:
        result = _JSON + json_str.encode("utf-8")
    return result


def _tidy3d_from_bytes(obj_bytes: bytes) -> _Tidy3dBaseModel:
    if obj_bytes.startswith(_JSON):
        obj = json.loads(obj_bytes[2:].decode("utf-8"))
    elif obj_bytes.startswith(_HDF5_HEADER):
        buffer = io.BytesIO(obj_bytes)
        obj = _Tidy3dBaseModel.dict_from_hdf5(buffer)
    else:
        raise RuntimeError(
            "Byte sequence does not represent a recognized Tidy3D object in this version."
        )
    return getattr(tidy3d, obj["type"]).parse_obj(obj)


def _isotropic_uniform(technology: Technology, classification: Literal["optical", "electrical"]):
    if not isinstance(technology.get_background_medium(classification), _IsotropicUniformTypes):
        return False
    return all(
        isinstance(e.get_medium(classification), _IsotropicUniformTypes)
        for e in technology.extrusion_specs
    )


def _updated_tidy3d(obj: Any, path: Sequence[str], value: Any) -> _Tidy3dBaseModel:
    if len(path) == 0:
        return value

    attr = path[0]
    path = path[1:]
    if attr.isdecimal():
        attr = int(attr)
        if not hasattr(obj, "__len__"):
            raise RuntimeError(
                f"Invalid 'simulation_updates' key: index found ({attr}) for non-sequence object: "
                f"{obj}"
            )
        obj = list(obj)
        obj[attr] = _updated_tidy3d(obj[attr], path, value)
        return obj

    return obj.copy(update={attr: _updated_tidy3d(getattr(obj, attr), path, value)})


def _align_and_overlap(data0: _MonitorData, data1: _MonitorData) -> numpy.ndarray:
    rotations = [(0, "+"), (1, "+"), (0, "-"), (1, "-")]
    dir0 = getattr(data0.monitor, "direction", None)
    if dir0 is None:
        dir0 = data0.monitor.store_fields_direction
    dir1 = getattr(data1.monitor, "direction", None)
    if dir1 is None:
        dir1 = data1.monitor.store_fields_direction
    r0 = rotations.index((data0.monitor.size.index(0), dir0))
    r1 = rotations.index((data1.monitor.size.index(0), dir1))
    rotation = (r1 - r0) % 4

    fields0 = data0.field_components
    fields1 = data1.field_components

    dims = fields0["Ez"].dims
    coords = {d: fields0["Ez"].coords[d].values.copy() for d in dims}
    center = (data0.monitor.center[0], data0.monitor.center[1])

    if rotation == 0:
        fields0 = {
            "Ex": fields0["Ex"].values,
            "Hx": fields0["Hx"].values,
            "Ey": fields0["Ey"].values,
            "Hy": fields0["Hy"].values,
            "Ez": fields0["Ez"].values,
            "Hz": fields0["Hz"].values,
        }
    elif rotation == 1:
        x = coords["x"]
        coords["x"] = -coords["y"]
        coords["y"] = x
        center = (-center[1], center[0])
        ix = dims.index("x")
        iy = dims.index("y")
        fields0 = {
            "Ex": numpy.swapaxes(-fields0["Ey"].values, ix, iy),
            "Hx": numpy.swapaxes(-fields0["Hy"].values, ix, iy),
            "Ey": numpy.swapaxes(fields0["Ex"].values, ix, iy),
            "Hy": numpy.swapaxes(fields0["Hx"].values, ix, iy),
            "Ez": numpy.swapaxes(fields0["Ez"].values, ix, iy),
            "Hz": numpy.swapaxes(fields0["Hz"].values, ix, iy),
        }
    elif rotation == 2:
        coords["x"] = -coords["x"]
        coords["y"] = -coords["y"]
        center = (-center[0], -center[1])
        fields0 = {
            "Ex": -fields0["Ex"].values,
            "Hx": -fields0["Hx"].values,
            "Ey": -fields0["Ey"].values,
            "Hy": -fields0["Hy"].values,
            "Ez": fields0["Ez"].values,
            "Hz": fields0["Hz"].values,
        }
    elif rotation == 3:
        x = coords["x"]
        coords["x"] = coords["y"]
        coords["y"] = -x
        center = (center[1], -center[0])
        ix = dims.index("x")
        iy = dims.index("y")
        fields0 = {
            "Ex": numpy.swapaxes(fields0["Ey"].values, ix, iy),
            "Hx": numpy.swapaxes(fields0["Hy"].values, ix, iy),
            "Ey": numpy.swapaxes(-fields0["Ex"].values, ix, iy),
            "Hy": numpy.swapaxes(-fields0["Hx"].values, ix, iy),
            "Ez": numpy.swapaxes(fields0["Ez"].values, ix, iy),
            "Hz": numpy.swapaxes(fields0["Hz"].values, ix, iy),
        }

    coords["x"] = coords["x"] + data1.monitor.center[0] - center[0]
    coords["y"] = coords["y"] + data1.monitor.center[1] - center[1]

    n, t = ("x", "y") if r1 % 2 == 0 else ("y", "x")
    tangential_components = ("E" + t, "H" + t, "Ez", "Hz")
    fields0 = {
        c: ScalarModeFieldDataArray(fields0[c], dims=dims, coords=coords)
        for c in tangential_components
    }

    coords1 = tidy3d.Coords(
        x=fields1["Ez"].coords["x"].values,
        y=fields1["Ez"].coords["y"].values,
        z=fields1["Ez"].coords["z"].values,
    )
    fields0 = {c: coords1.spatial_interp(fields0[c], "linear") for c in tangential_components}

    sign = -1 if r1 == 1 or r1 == 2 else 1
    d_area = sign * data1._diff_area
    e0_h1 = fields0["E" + t] * fields1["Hz"] - fields0["Ez"] * fields1["H" + t]
    e1_h0 = fields1["E" + t] * fields0["Hz"] - fields1["Ez"] * fields0["H" + t]
    integrand = (e0_h1 + e1_h0) * d_area
    overlap = 0.25 * integrand.sum(dim=d_area.dims).isel({n: 0}, drop=True).values

    # Modes are normalized by the mode solver, so the overlap should be only a phase difference.
    # We normalize the result to remove numerical errors introduced by the grid interpolation.
    overlap_mag = numpy.abs(overlap)
    if not numpy.allclose(overlap_mag, 1.0, atol=0.1):
        max_err = overlap_mag.flat[numpy.argmax(numpy.abs(overlap_mag - 1.0))]
        warnings.warn(
            f"Modal overlap calculation resulted in an unexpected magnitude ({max_err}). Consider "
            "increasing the mesh refinement for the mode solver.",
            RuntimeWarning,
            2,
        )

    return overlap / overlap_mag


_sim_data_classes = {
    "fdtd": (tidy3d.Simulation, tidy3d.SimulationData),
    "ms": (ModeSolver, tidy3d.ModeSolverData),
    "eme": (tidy3d.EMESimulation, tidy3d.EMESimulationData),
}
_prefixes = {v[0].__name__: k for k, v in _sim_data_classes.items()}
_sim_types = Union[tuple(v[0] for v in _sim_data_classes.values())]  # noqa: UP007
_data_types = Union[tuple(v[1] for v in _sim_data_classes.values())]  # noqa: UP007


class _Tidy3DTaskRunner:
    def __init__(
        self,
        simulation: _sim_types,
        task_name: str,
        remote_path: str,
        data_path: str,
        verbose: bool,
        cost_estimation: bool,
    ):
        self.prefix = _prefixes[simulation.type]
        self.simulation = simulation.copy()  # For thread safety
        self.task_name = task_name
        self.remote_path = remote_path
        self.data_path = data_path
        self.verbose = verbose
        self.cost_estimation = cost_estimation
        self.task_id = "tidy3d" if _local_tidy3d_solver else None
        self._data = None
        self._suffix = _safe_hash(
            _tidy3d_to_bytes(simulation) + task_name.encode("utf-8") + remote_path.encode("utf-8")
        )
        self.lock = threading.Lock()
        self.thread = None

        self.data_path.mkdir(parents=True, exist_ok=True)

        # Use cached data, if available
        info_file = self.info_file()
        sim_file = self.sim_file()
        data_file = self.data_file()
        if info_file.is_file() and sim_file.is_file() and data_file.is_file():
            info = json.loads(info_file.read_text())
            if (
                self.task_name == info["task_name"]
                and self.remote_path == info["remote_path"]
                and str(self.data_path) == info["data_path"]
            ):
                if verbose:
                    print(f"Loading cached simulation from {info_file!s}.")
                data_class = _sim_data_classes[self.prefix][1]
                self._data = data_class.from_file(str(data_file))
                self.task_id = info["task_id"]
                self._status = {
                    "progress": 100,
                    "message": "success",
                    "tasks": {self.task_id: {"task_name": self.task_name, "status": "success"}},
                }
                return

        if _local_tidy3d_solver:
            from tidy3d_pipeline.run import run, run_mode_solver  # noqa: PLC0415

            if self.prefix == "ms":
                self._data = run_mode_solver(self.simulation, str(self.data_file()))
            else:
                self._data = run(self.simulation, str(self.data_file()))
            self._status = {
                "progress": 100,
                "message": "success",
                "tasks": {self.task_id: {"task_name": self.task_name, "status": "success"}},
            }
            info = {
                "task_id": self.task_id,
                "task_name": self.task_name,
                "remote_path": self.remote_path,
                "data_path": str(self.data_path),
            }
            self.info_file().write_text(json.dumps(info))
            self.simulation.to_hdf5(str(self.sim_file()))
        else:
            from tidy3d import web  # noqa: PLC0415

            # Make sure the folder is created before we use multithreaded uploads to avoid
            # duplication and name errors
            web.api.webapi.Folder.get(remote_path, create=True)

            self._task_info = {"task_name": self.task_name}
            self._status = {
                "progress": 0,
                "message": "running",
                "tasks": {"unknown": self._task_info},
            }

            self.thread = threading.Thread(daemon=True, target=self._run_and_monitor_task)
            self.thread.start()

    def _set_status(self, progress, message, task_info_update):
        with self.lock:
            self._status["progress"] = progress
            self._status["message"] = message
            self._task_info.update(task_info_update)

    def _run_and_monitor_task(self):
        from tidy3d import web  # noqa: PLC0415
        from tidy3d.web import estimate_cost  # noqa: PLC0415
        from tidy3d.web.api import webapi  # noqa: PLC0415
        from tidy3d.web.core.exceptions import WebError  # noqa: PLC0415

        # Upload and get task ID
        if self.verbose:
            print(f"Uploading task '{self.task_name}…'")
        try:
            self.task_id = web.upload(
                simulation=self.simulation,
                task_name=self.task_name,
                folder_name=self.remote_path,
                reduce_simulation=True,
                verbose=False,
            )
        except Exception as err:
            self._set_status(100, "error", {"error": str(err)})
            return

        with self.lock:
            self._status["tasks"] = {self.task_id: self._task_info}

        if self.cost_estimation:
            try:
                cost = estimate_cost(self.task_id, verbose=False)
            except WebError as err:
                self._set_status(100, "error", {"error": str(err)})
                return
            if self.verbose:
                print(f"Estimated cost for task '{self.task_name}: {cost}'")
            self._set_status(100, "success", {"estimated_cost": cost})
            return

        # Start task
        self._set_status(2, "running", {"status": "queued"})
        if self.verbose:
            url = webapi._get_url(self.task_id)
            print(f"Starting task '{self.task_name}': {url}")
        try:
            web.start(self.task_id)
        except WebError as err:
            self._set_status(100, "error", {"error": str(err)})
            return

        with _pending_tasks_lock:
            _pending_tasks.add(self.task_id)

        # Monitor progress
        goon = True
        while goon:
            time.sleep(TIDY3D_POLLING_INTERVAL)

            try:
                info = web.get_info(self.task_id, verbose=False)
            except WebError as err:
                self._set_status(100, "error", {"error": str(err)})
                return

            if info.status in ("error", "diverged", "deleted", "abort", "aborted", "aborting"):
                warnings.warn(
                    f"Task with taskId={self.task_id} returned status '{info.status}'.",
                    stacklevel=2,
                )
                with _pending_tasks_lock:
                    _pending_tasks.discard(self.task_id)
                self._set_status(100, "error", {"status": info.status})
                return

            if info.status == "success":
                goon = False

                with _pending_tasks_lock:
                    _pending_tasks.discard(self.task_id)

                self._set_status(98, "running", {"status": "success"})

                with self.lock:
                    info_file_data = {
                        "task_id": self.task_id,
                        "task_name": self.task_name,
                        "remote_path": self.remote_path,
                        "data_path": str(self.data_path),
                    }
                    self.info_file().write_text(json.dumps(info_file_data))

                    sim_file = self.sim_file()
                    if not sim_file.is_file():
                        self.simulation.to_hdf5(str(sim_file))
            else:
                try:
                    run_info = webapi.get_run_info(self.task_id)
                except WebError as err:
                    self._set_status(100, "error", {"error": str(err)})
                    return
                self._set_status(
                    2 + 0.96 * run_info[0],
                    "running",
                    {"status": info.status, "progress": run_info[0]},
                )

        # Download result
        if self.verbose:
            print(f"Downloading data from '{self.task_name}'…")
        try:
            data = web.load(task_id=self.task_id, path=str(self.data_file()), verbose=False)
        except Exception as err:
            with self.lock:
                self._set_status(100, "error", {"error": str(err)})
            return

        with self.lock:
            self._data = data
            self._status["progress"] = 100
            self._status["message"] = "success"

    def info_file(self) -> pathlib.Path:
        return self.data_path / f"{self.prefix}_info-{self._suffix}.json"

    def sim_file(self) -> pathlib.Path:
        return self.data_path / f"{self.prefix}-{self._suffix}.hdf5"

    def data_file(self) -> pathlib.Path:
        return self.data_path / f"{self.prefix}_data-{self._suffix}.hdf5"

    @property
    def status(self) -> dict[str, Any]:
        with self.lock:
            return self._status

    @property
    def data(self) -> _data_types:
        with self.lock:
            if self._data is None and self._status["message"] != "success":
                raise RuntimeError(
                    f"Tidy3D task with taskId={self.task_id} did not complete successfully."
                )
            return self._data


# This function is used for 2 reasons: first, it checks if the local mode solver should be used.
# The check could be done in _Tidy3DTaskRunner, but that would increase its complexity. Second,
# web GUI can overwrite it to customize how simulations are executed.
def _simulation_runner(
    *,
    simulation: _sim_types,
    task_name: str,
    remote_path: str,
    data_path: str,
    verbose: bool,
    cost_estimation: bool,
) -> Any:
    if not _local_tidy3d_solver and use_local_mode_solver and simulation.type == "ModeSolver":
        old_level = tidy3d.config.logging_level
        tidy3d.config.logging_level = "ERROR"
        data = simulation.solve()
        tidy3d.config.logging_level = old_level
        RunnerResult = collections.namedtuple("RunnerResult", ("status", "data"))
        return RunnerResult(status={"progress": 100, "message": "success"}, data=data)
    return _Tidy3DTaskRunner(
        simulation, task_name, remote_path, data_path, verbose, cost_estimation
    )


class _ModeSolverRunner:
    def __init__(
        self,
        port: Port | FiberPort | PortSpec | ModeSolver,
        frequencies: Sequence[float],
        mesh_refinement: float | None,
        technology: Technology,
        *,
        task_name: str | None = None,
        remote_path: str = "Mode Solver",
        center_in_origin: bool = True,
        cost_estimation: bool = False,
        verbose: bool = True,
    ):
        if mesh_refinement is None:
            mesh_refinement = config.default_mesh_refinement

        frequencies = numpy.array(frequencies, dtype=float, ndmin=1)
        classification = frequency_classification(frequencies)

        if isinstance(port, Port):
            if center_in_origin:
                port = port.copy()
                port.center = (0, 0)
            mode_solver = port.to_tidy3d_mode_solver(
                frequencies,
                mesh_refinement,
                technology=technology,
                use_angle_rotation=_isotropic_uniform(technology, classification),
            )
            description = port.spec.description
        elif isinstance(port, FiberPort):
            if center_in_origin:
                port = port.copy()
                port.center = (0, 0, 0)
            mode_solver = port.to_tidy3d_mode_solver(
                frequencies,
                mesh_refinement,
                technology=technology,
                use_angle_rotation=_isotropic_uniform(technology, classification),
            )
            description = "FiberPort"
        elif isinstance(port, PortSpec):
            mode_solver = port.to_tidy3d(frequencies, mesh_refinement, technology=technology)
            description = port.description
        elif isinstance(port, ModeSolver):
            mode_solver = port
            description = "ModeSolver"
        else:
            raise TypeError("'port' must be a Port, FiberPort, PortSpec, or ModeSolver instance.")

        mode_solver_bytes = _tidy3d_to_bytes(mode_solver)
        key = (mode_solver_bytes, remote_path, cost_estimation)
        self.runner = _mode_solver_cache[key]
        if self.runner is None or self.runner.status["message"] == "error":
            suffix = _safe_hash(mode_solver_bytes)
            if task_name is None:
                task_name = _filename_cleanup("Mode-" + description)
            self.runner = _simulation_runner(
                simulation=mode_solver,
                task_name=task_name,
                remote_path=remote_path,
                data_path=_cache_path(suffix),
                cost_estimation=cost_estimation,
                verbose=verbose,
            )
            _mode_solver_cache[key] = self.runner

    @property
    def status(self) -> dict[str, Any]:
        return self.runner.status

    @property
    def data(self) -> tidy3d.SimulationData | tidy3d.ModeSolverData:
        return self.runner.data


def port_modes(
    port: str | Port | FiberPort | PortSpec | ModeSolver,
    frequencies: Sequence[float] = (),
    mesh_refinement: float | None = None,
    group_index: bool = False,
    impedance: bool = False,
    technology: Technology | None = None,
    task_name: str | None = None,
    remote_path: str = "Mode Solver",
    verbose: bool = True,
    show_progress: bool = True,
) -> ModeSolver:
    """Compute the port modes using Tidy3D's mode solver.

    Args:
        port: Port or port specification to solver for modes. A Tidy3D
          ``ModeSolver`` instance can also be used.
        frequencies: Sequence of frequency values for the mode solver.
          Not required if a ``ModeSolver`` instance is used as 'port'.
        mesh_refinement: Minimal number of mesh elements per wavelength used
          for mode solving.
        group_index: Flag indicating whether the mode solver should include
          group index computation.
        impedance: Flag indicating whether the mode impedances should also
          be computed and returned.
        technology: Technology specification for the port.
        task_name: Name for the Tidy3D task.
        remote_path: Remote folder for the task.
        verbose: Flag controlling solver verbosity.
        show_progress: Flag to control whether to show solver progress.

    Returns:
        Mode solver object with calculated `data`. If ``impedance == True``,
        the calculated impedance is also returned (``None`` for optical
        modes).

    Note:
        If a ``ModeSolver`` instance is used as 'port', arguments
        'frequency', 'mesh_refinement', 'group_index', and 'technology' have
        no effect.
    """
    if technology is None:
        technology = config.default_technology
    if isinstance(port, str):
        port = technology.ports[port]

    classification = None
    if isinstance(port, (Port, FiberPort)):
        classification = port.classification
        mode_solver = port.to_tidy3d_mode_solver(
            frequencies,
            mesh_refinement,
            group_index,
            technology,
            _isotropic_uniform(technology, classification),
        )
    elif isinstance(port, PortSpec):
        mode_solver = port.to_tidy3d(frequencies, mesh_refinement, group_index, technology)
        classification = port.classification
    elif isinstance(port, ModeSolver):
        mode_solver = port
    else:
        raise TypeError("'port' must be a Port, FiberPort, PortSpec, or ModeSolver instance.")

    runner = _ModeSolverRunner(
        mode_solver,
        frequencies,
        mesh_refinement,
        technology,
        task_name=task_name,
        remote_path=remote_path,
        center_in_origin=False,
        verbose=verbose,
    )

    if show_progress:
        print("Starting…", end="\r", flush=True)

    progress_chars = "-\\|/"
    i = 0
    while True:
        status = runner.status
        message = status["message"]
        if message == "success":
            if show_progress:
                print("Progress: 100% ", end="\n", flush=True)
            mode_solver._patch_data(runner.data)
            if not impedance:
                return mode_solver

            z0 = None
            if classification == "electrical":
                ic = port.to_tidy3d_impedance_calculator()
                z0 = ic.compute_impedance(mode_solver.data)
            return mode_solver, z0
        elif message == "running":
            if _local_tidy3d_solver:
                raise RuntimeError("Unexpected on-prem mode solver message.")
            if show_progress:
                p = max(0, min(100, int(status.get("progress", 0))))
                c = progress_chars[i]
                i = (i + 1) % len(progress_chars)
                print(f"Progress: {p}% {c}", end="\r", flush=True)
            time.sleep(0.3)
        elif message == "error":
            if show_progress:
                print("Progress: error", end="\n", flush=True)
            raise RuntimeError("Mode solver run resulted in error.")
        else:
            raise RuntimeError(f"Status message unknown: {message:r}.")


def _inner_product(
    field_data: _ElectromagneticFieldData,
    port: GaussianPort,
    epsilon_r: float,
    conjugate: bool = True,
) -> numpy.ndarray:
    normal = field_data.monitor.size.index(0)

    freqs = field_data.Ex.coords["f"].values
    x = field_data.Ex.coords["x"].values
    y = field_data.Ex.coords["y"].values
    z = field_data.Ex.coords["z"].values

    shape = [x.size, y.size, z.size]
    shape.pop(normal)
    shape = (*shape, freqs.size)

    dim_names = ["x", "y", "z", "f"]
    dim_names.pop(normal)

    dims = [0, 1, 2]
    dims.pop(normal)

    d_area = field_data._diff_area.transpose(*dim_names[:-1]).values

    fields_a = field_data._colocated_tangential_fields
    ea = (
        fields_a["E" + dim_names[0]].transpose(*dim_names).values,
        fields_a["E" + dim_names[1]].transpose(*dim_names).values,
    )
    ha = (
        fields_a["H" + dim_names[0]].transpose(*dim_names).values,
        fields_a["H" + dim_names[1]].transpose(*dim_names).values,
    )

    del fields_a

    # This comes from ElectromagneticFieldData._tangential_corrected()
    if normal == 1:
        ha = (-ha[0], -ha[1])

    x, y, z = numpy.meshgrid(x, y, z, indexing="ij")
    field_profile, e0, h0, e_pol, h_pol = port.fields(
        x.flatten(), y.flatten(), z.flatten(), freqs, epsilon_r
    )
    del x, y, z

    field_profile = field_profile.reshape(shape)
    if conjugate:
        field_profile = field_profile.conj()

    e_x_h = field_profile * (
        h0 * (h_pol[dims[1]] * ea[0] - h_pol[dims[0]] * ea[1])
        + e0 * (e_pol[dims[0]] * ha[1] - e_pol[dims[1]] * ha[0])
    )

    return 0.25 * (d_area[..., numpy.newaxis] * e_x_h).sum((0, 1))


def _get_amps(
    data: _ElectromagneticFieldData,
    port: Port | FiberPort | GaussianPort,
    epsilon_r: float,
    mode_index: int,
    reversed: bool,
) -> numpy.ndarray:
    if isinstance(port, (Port, FiberPort)):
        _, _, direction, *_ = port._axis_aligned_properties()
        direction = "-" if (direction == "+") == reversed else "+"
        amps = data.amps.sel(direction=direction, mode_index=mode_index).values.flatten()
        return amps

    if reversed:
        port = port.reflected()
    return _inner_product(data, port, epsilon_r)


def _requires_mode_remap(
    symmetry: tuple[int, int, int], mode_monitors: Iterable[tidy3d.ModeMonitor]
) -> bool:
    return symmetry != (0, 0, 0) or any(m.mode_spec.filter_pol is not None for m in mode_monitors)


def _mode_remap_from_symmetry(
    elements: dict[str, numpy.ndarray],
    ports: dict[str, Port | GaussianPort],
    data_sym: dict[str, tidy3d.ModeData | tidy3d.ModeSolverData],
    data_full: dict[str, tidy3d.ModeData | tidy3d.ModeSolverData],
) -> dict[tuple[str, str], numpy.ndarray]:
    num_freqs = next(iter(elements.values())).size
    mode_names = [
        f"{name}@{index}"
        for name, port in sorted(ports.items())
        for index in range(port.num_modes + port.added_solver_modes)
    ]

    # Port mode transformation matrix
    # M_ij = <e_i, e_j'> / <e_i, e_i>
    # S' = pinv(M) × S × M
    s = numpy.zeros((num_freqs, len(mode_names), len(mode_names)), dtype=complex)
    m = numpy.zeros((num_freqs, len(mode_names), len(mode_names)), dtype=complex)

    for j, mode_in in enumerate(mode_names):
        for i, mode_out in enumerate(mode_names):
            element = elements.get((mode_in, mode_out))
            if element is not None:
                s[:, i, j] = element

    total_modes = 0
    total_columns = 0
    invalid_sym_modes = []
    for name, port in sorted(ports.items()):
        num_modes = port.num_modes + port.added_solver_modes
        if isinstance(port, GaussianPort):
            m[
                :, total_modes : total_modes + num_modes, total_columns : total_columns + num_modes
            ] = numpy.eye(num_modes, dtype=complex)
            total_columns += num_modes
        else:
            sym_mode = data_sym[name]
            full_mode = data_full[name]
            projection = sym_mode.outer_dot(full_mode, conjugate=False)
            norm = sym_mode.dot(sym_mode, conjugate=False)
            m_block = (
                projection.transpose("mode_index_1", "mode_index_0", "f").values
                / norm.transpose("mode_index", "f").values
            ).T
            for sym_index in range(num_modes):
                m_line = m_block[:, sym_index, :num_modes]
                if (
                    numpy.sqrt((numpy.abs(m_line) ** 2).sum(axis=1)).sum()
                    < OVERLAP_THRESHOLD * num_freqs
                ):
                    invalid_sym_modes.append(total_modes + sym_index)
            for full_index in range(num_modes):
                m_column = m_block[:, :num_modes, full_index]
                if (
                    numpy.sqrt((numpy.abs(m_column) ** 2).sum(axis=1)).sum()
                    < OVERLAP_THRESHOLD * num_freqs
                ):
                    mode_names.pop(total_columns)
                else:
                    m[:, total_modes : total_modes + num_modes, total_columns] = m_column
                    total_columns += 1
        total_modes += num_modes

    m = m[:, :, :total_columns]
    if len(invalid_sym_modes) > 0:
        m = numpy.delete(m, invalid_sym_modes, 1)
        s = numpy.delete(s, invalid_sym_modes, 1)
        s = numpy.delete(s, invalid_sym_modes, 2)

    s = numpy.linalg.pinv(m) @ s @ m
    return {
        (mode_in, mode_out): s[:, i, j]
        for j, mode_in in enumerate(mode_names)
        for i, mode_out in enumerate(mode_names)
    }


class _Tidy3DModelRunner:
    def __init__(
        self,
        frequencies: Sequence[float],
        simulations: tidy3d.Simulation,
        ports: dict[str, Port | FiberPort | GaussianPort],
        port_epsilon: dict[str, float],
        element_mappings: Sequence[_PerElementMap],
        folder_name: str,
        data_path: str,
        batch_file: str,
        cost_estimation: bool,
        verbose: bool,
    ):
        self.frequencies = frequencies
        self.runners = {}
        for name, sim in simulations.items():
            key = (_tidy3d_to_bytes(sim), folder_name, data_path, cost_estimation)
            runner = _tidy3d_model_cache[key]
            if runner is None or runner.status["message"] == "error":
                runner = _simulation_runner(
                    simulation=sim,
                    task_name=name,
                    remote_path=folder_name,
                    data_path=data_path,
                    cost_estimation=cost_estimation,
                    verbose=verbose,
                )
                _tidy3d_model_cache[key] = runner
            self.runners[name] = runner

        self.ports = ports
        self.port_epsilon = port_epsilon
        self.element_mappings = element_mappings
        self.batch_file = batch_file
        self.verbose = verbose
        self._s_matrix = None

        # If the model uses any symmetry or polarization filter, it will impact the mode numbering
        # of the ports. We need to remap port modes from the symmetry-applied to the full version.
        # The first simulation contains all mode fields with symmetry, so we only need to solve for
        # the modes in the full version.
        self.mode_data_key = sorted(simulations)[0]
        mode_sim = simulations[self.mode_data_key]
        self.mode_remap = _requires_mode_remap(
            mode_sim.symmetry,
            (m for m in mode_sim.monitors if m.name in ports and isinstance(m, tidy3d.ModeMonitor)),
        )
        if self.mode_remap:
            mode_sim = mode_sim.copy(update={"symmetry": (0, 0, 0)})
            for monitor in mode_sim.monitors:
                if not isinstance(monitor, tidy3d.ModeMonitor):
                    continue
                mode_solver = ModeSolver(
                    simulation=mode_sim,
                    plane=monitor.bounding_box,
                    mode_spec=monitor.mode_spec.copy(update={"filter_pol": None}),
                    freqs=monitor.freqs,
                    direction=monitor.store_fields_direction,
                )
                self.runners[monitor.name] = _simulation_runner(
                    simulation=mode_solver,
                    task_name=monitor.name,
                    remote_path=folder_name,
                    data_path=data_path,
                    cost_estimation=cost_estimation,
                    verbose=verbose,
                )

    @property
    def status(self) -> dict[str, Any]:
        """Monitor S matrix computation progress."""
        from tidy3d.web import BatchData  # noqa: PLC0415

        if self.batch_file is not None:
            all_available = True
            task_paths = {}
            task_ids = {}
            for name, runner in self.runners.items():
                if isinstance(runner, _Tidy3DTaskRunner):
                    if runner.task_id is None:
                        all_available = False
                        break
                    task_paths[name] = str(runner.data_file())
                    task_ids[name] = runner.task_id

            if all_available:
                if len(task_ids) > 0:
                    BatchData(
                        task_paths=task_paths, task_ids=task_ids, verbose=self.verbose
                    ).to_file(str(self.batch_file))
                self.batch_file = None

        all_stat = [runner.status for runner in self.runners.values()]
        tasks = {}
        for s in all_stat:
            tasks.update(s.get("tasks", {}))

        if all(s["message"] == "success" for s in all_stat):
            message = "success"
            progress = 100
        elif any(s["message"] == "error" for s in all_stat):
            message = "error"
            progress = 100
        else:
            message = "running"
            progress = sum(
                100 if s["message"] == "success" else s["progress"] for s in all_stat
            ) / len(all_stat)
        return {"progress": progress, "message": message, "tasks": tasks}

    @property
    def s_matrix(self) -> SMatrix:
        """Get the model S matrix."""
        if self._s_matrix is None:
            elements = {}
            for src, src_port in self.ports.items():
                for src_mode in range(src_port.num_modes):
                    src_key = f"{src}@{src_mode}"
                    if src_key not in self.runners:
                        continue
                    data = self.runners[src_key].data
                    norm = _get_amps(
                        data[src], src_port, self.port_epsilon.get(src), src_mode, False
                    )
                    for dst, dst_port in self.ports.items():
                        for dst_mode in range(dst_port.num_modes):
                            dst_key = f"{dst}@{dst_mode}"
                            coeff = _get_amps(
                                data[dst], dst_port, self.port_epsilon.get(dst), dst_mode, True
                            )
                            elements[(src_key, dst_key)] = coeff / norm

            # S[src2@i, dst2@j] = factor[i, j] * S[src1@i, dst1@j]
            for (src1, dst1), (src2, dst2), factor in self.element_mappings:
                src_modes = self.ports[src1].num_modes
                dst_modes = self.ports[dst1].num_modes
                for src_index in range(src_modes):
                    for dst_index in range(dst_modes):
                        key1 = f"{src1}@{src_index}", f"{dst1}@{dst_index}"
                        key2 = f"{src2}@{src_index}", f"{dst2}@{dst_index}"
                        if key1 in elements and key2 not in elements:
                            elements[key2] = factor[src_index, dst_index] * elements[key1]

            # If symmetry or polarization filter was used, calculate and apply mode mapping
            if self.mode_remap:
                data_sym = self.runners[self.mode_data_key].data
                data_full = {
                    name: self.runners[name].data
                    for name, port in self.ports.items()
                    if not isinstance(port, GaussianPort)
                }
                elements = _mode_remap_from_symmetry(elements, self.ports, data_sym, data_full)

            self._s_matrix = SMatrix(self.frequencies, elements, self.ports)

        return self._s_matrix


def _get_epsilon(
    position: Sequence[float],
    structures: Sequence[tidy3d.Structure],
    background_medium: pft.Medium,
    frequencies: Sequence[float],
) -> numpy.ndarray:
    for structure in structures[::-1]:
        bb_min, bb_max = structure.geometry.bounds
        if all(
            bb_min[i] <= position[i] <= bb_max[i] for i in range(3)
        ) and structure.geometry.inside(position[0:1], position[1:2], position[2:3]):
            return numpy.array([structure.medium.eps_comp(0, 0, f).real for f in frequencies])
    return numpy.array([background_medium.eps_comp(0, 0, f).real for f in frequencies])


def _source_shift(
    source: tidy3d.Source,
    simulation_grid: tidy3d.Grid,
    gap: float,
    port: Port | FiberPort | GaussianPort,
) -> tidy3d.Source:
    axis = source.size.index(0)
    center = list(source.center)
    if gap > 0:
        center[axis] += -gap if source.direction == "+" else gap
    else:
        grid_steps = -2 if source.direction == "+" else 2

        grid_boundaries = simulation_grid.boundaries.to_list[axis]
        grid_centers = simulation_grid.centers.to_list[axis]

        before = numpy.argwhere(grid_boundaries < center[axis])
        if len(before) == 0:
            raise RuntimeError(f"Position {center[axis]} is outside of simulation bounds.")

        shifted_index = before.flat[-1] + grid_steps
        if (grid_steps < 0 and shifted_index < 0) or (
            grid_steps > 0 and shifted_index >= len(grid_centers)
        ):
            raise RuntimeError(f"Position {center[axis]} is too close to {'xyz'[axis]} boundary.")

        center[axis] = float(grid_centers[shifted_index])

    if isinstance(source, tidy3d.GaussianBeam):
        input_vector = port.input_vector
        offset = abs((center[axis] - source.center[axis]) / input_vector[axis])
        center = source.center - input_vector * offset
        update = {
            "center": center.tolist(),
            "waist_distance": float(source.waist_distance - offset),
        }
        if input_vector[axis] < 1.0:
            update["num_freqs"] = 1
    else:
        update = {"center": center}

    return source.copy(update=update)


def _geometry_key(geom: tidy3d.Geometry) -> tuple[float, float, float, float, str]:
    return (*(x for corner in geom.bounds for x in corner), geom.type)


def _inner_geometry_sort(geom: tidy3d.Geometry) -> tidy3d.Geometry:
    if isinstance(geom, tidy3d.GeometryGroup):
        return tidy3d.GeometryGroup(
            geometries=sorted([_inner_geometry_sort(g) for g in geom.geometries], key=_geometry_key)
        )
    elif isinstance(geom, tidy3d.ClipOperation):
        return tidy3d.ClipOperation(
            operation=geom.operation,
            geometry_a=_inner_geometry_sort(geom.geometry_a),
            geometry_b=_inner_geometry_sort(geom.geometry_b),
        )
    return geom


class Tidy3DModel(Model):
    """S matrix model based on Tidy3D FDTD calculation.

    Args:
        run_time: Maximal simulation run-time (in seconds) or an instance of
          ``tidy3d.RuntImeSpec``.
        medium: Background medium. If ``None``, the technology default is
          used.
        symmetry: Component symmetries.
        boundary_spec: Simulation boundary specifications (absorber by
          default).
        monitors: Extra field monitors added to the simulation.
        structures: Additional structures included in the simulations.
        grid_spec: Simulation grid specification. A single float can be used
          to specify the ``min_steps_per_wvl`` for an auto grid.
        shutoff: Field decay factor for simulation termination.
        subpixel: Flag controlling subpixel averaging in the simulation
          grid or an instance of ``tidy3d.SubpixelSpec``.
        courant: Courant stability factor.
        port_symmetries: Port symmetries to reduce the number of simulation
          runs. See note below.
        bounds: Bound overrides for the final simulation in the form
          ``((xmin, ymin, zmin), (xmax, ymax, zmax))``. Values set to
          ``None`` are ignored.
        source_gap: Separation between source and monitor representing a
          component port. Defaults to 2 grid cells for optical simulations
          and 1% of the maximum wavelength for electrical ones. The defaults
          are used when this is unset or set to 0.
        simulation_updates: Dictionary of updates applied to all simulations
          generated by this model. See example below.
        verbose: Control solver verbosity.

    If not set, the default grid specification for the component simulations
    is defined based on the wavelengths used in the ``s_matrix`` call.
    Defaults for ``run_time``, ``boundary_spec``, ``shutoff``, ``subpixel``,
    ``courant``, and ``source_gap`` can be defined in a ``"tidy3d"``
    dictionary in :attr:`config.default_kwargs`. Note that the values used
    are the ones available at the time of the ``s_matrix`` or ``start``
    call, not when model is initialized.

    The ``start`` method accepts an ``inputs`` argument as a sequence or set
    of port names to limit the computation to those inputs. Instead of port
    names, ``{port}@{mode}`` specifications are also accepted.

    Note:
        Each item in the ``port_symmetries`` sequence is a tuple of port
        names indicating the port replacements that do not affect the S
        matrix computation. Usually, that means each item is a permutation
        of the *sorted* list of component ports.

        For example, in a Y junction with input "P0" and outputs "P1" and
        "P2" operating in the fundamental TE mode, we can exchange ports
        "P1" and "P2" and the S matrix remains the same, because S₁₀ = S₂₀
        and S₁₁ = S₂₂. This symmetry is represented as the sequence
        ``("P0", "P2", "P1")``, which exchange "P1" anf "P2" with respect
        to the *sorted* port list "P0", "P1", "P2". We could also use
        indices instead of port names to the same effect: ``(0, 2, 1)``.

        It is also possible to represent S matrix symmetries for individual
        elements and with correction factors. This form requires a
        reference element, a mapped element, and a multiplication factor:
        ``((src, dst1), (src2, dst2), c)``, which translates into
        ``S[src2@i, dst2@j] = c[i,j] * S[src1@i, dst1@j]`` for all mode
        indices ``i`` and ``j`` supported by the source and destination
        ports, respectively. Note that the multiplicative factor is an array
        so that each mode can be phase-compensated according to its field
        symmetry (if ``c`` is an scalar, all modes use the same value).

    Example:
        Keys in ``simulation_updates`` specify a path to the value that
        will be updated using a ``'/'`` as separator, analogously to the
        ``path`` argument in the ``updated_copy`` method from ``tidy3d``
        objects. For indexing into a tuple or list, an integer value is
        used. The first part of the path can be an input in the form
        ``port@mode`` to specify that the update should be applied to
        a that simulation only.

        >>> simulation_updates = {
        ...     "P0@0/grid_spec/grid_x/max_scale": 1.3,
        ...     "boundary_spec/z/plus": td.PML(),
        ...     "center/2": 0.0,
        ... }
        >>> model = pf.Tidy3DModel(simulation_updates=simulation_updates)

    See also:
        - `Tidy3D Model guide <../guides/Tidy3D_Model.ipynb>`__
        - `Y splitter example <../examples/Y_Splitter.ipynb>`__
    """

    def __init__(
        self,
        run_time: tidy3d.RunTimeSpec | float | None = None,
        medium: pft.Medium | None = None,
        symmetry: _SymmetryType = (0, 0, 0),
        boundary_spec: tidy3d.BoundarySpec | None = None,
        monitors: Sequence[_MonitorType] = (),
        structures: Sequence[tidy3d.Structure] = (),
        grid_spec: pft.PositiveFloat | tidy3d.GridSpec | None = None,
        shutoff: pft.PositiveFloat | None = None,
        subpixel: _SubpixelType | None = None,
        courant: pft.Fraction | None = None,
        port_symmetries: _PortSymmetryType = (),
        bounds: _BoundsType = ((None, None, None), (None, None, None)),
        source_gap: pft.NonNegativeFloat | None = None,
        simulation_updates: dict[str, Any] = {},
        verbose: bool = True,
    ):
        super().__init__(
            run_time=run_time,
            medium=medium,
            symmetry=symmetry,
            boundary_spec=boundary_spec,
            monitors=monitors,
            structures=structures,
            grid_spec=grid_spec,
            shutoff=shutoff,
            subpixel=subpixel,
            courant=courant,
            port_symmetries=port_symmetries,
            bounds=bounds,
            source_gap=source_gap,
            simulation_updates=simulation_updates,
            verbose=verbose,
        )
        self.run_time = run_time
        self.medium = medium
        self.symmetry = symmetry
        self.boundary_spec = boundary_spec
        self.monitors = monitors
        self.structures = structures
        self.grid_spec = grid_spec
        self.shutoff = shutoff
        self.subpixel = subpixel
        self.courant = courant
        self.port_symmetries = port_symmetries
        self.bounds = bounds
        self.source_gap = source_gap
        self.simulation_updates = simulation_updates
        self.verbose = verbose

    def data_path_for(self, component: Component, *, _skip_warning=False) -> pathlib.Path:
        """DEPRECATED: Use Tidy3DModel.batch_data."""
        if not _skip_warning:
            warnings.warn(
                "Methods 'batch_data_for', 'batch_file_for', and 'data_path_for' are deprecated "
                "and they will be removed in the next release. Use 'Tidy3DModel.batch_data' to "
                "retrieve simulation data.",
                FutureWarning,
                stacklevel=2,
            )
        return _cache_path(_safe_hash(component.name.encode("utf-8")))

    def batch_file_for(self, component: Component, *, _skip_warning=False) -> pathlib.Path:
        """DEPRECATED: Use Tidy3DModel.batch_data."""
        try:
            suffix = _safe_hash(_content_repr(component))
        except Exception:
            suffix = _safe_hash(component.name.encode("utf-8"))
        return (
            self.data_path_for(component, _skip_warning=_skip_warning) / f"batch_data-{suffix}.json"
        )

    def batch_data_for(self, component: Component, *, _skip_warning=False) -> Any | None:
        """DEPRECATED: Use Tidy3DModel.batch_data."""
        batch_file = self.batch_file_for(component, _skip_warning=_skip_warning)
        if batch_file.is_file():
            from tidy3d.web import BatchData  # noqa: PLC0415

            batch_data = BatchData.from_file(str(batch_file))
            if _local_tidy3d_solver:
                return {
                    name: tidy3d.SimulationData.from_file(path)
                    for name, path in batch_data.task_paths.items()
                }
            return batch_data
        return None

    def _process_port_symmetries(
        self, ports: dict[str, Port | FiberPort | GaussianPort], component_name: str
    ) -> tuple[set[str], list[_PerElementMap]]:
        """Return the required simulation sources and mappings for a component."""
        port_names = sorted(ports.keys())
        element_mappings = []
        # required_sources = set(port_names)

        for port_symmetry in self.port_symmetries:
            # _ImplicitMap
            if all(isinstance(x, (str, int)) for x in port_symmetry):
                equiv = [
                    port_names[x] if not isinstance(x, str) and x < len(port_names) else x
                    for x in port_symmetry
                ]
                pairs = []
                for src1, src2 in zip(port_names, equiv, strict=False):
                    src1_port = ports.get(src1)
                    src2_port = ports.get(src2)
                    if src1_port is None or src2_port is None:
                        missing_port = src1 if src1_port is None else src2
                        warnings.warn(
                            f"Port {missing_port} specified in 'port_symmetries' does not exist in "
                            f"component {component_name} or is defined for a different frequency "
                            f"range.",
                            stacklevel=3,
                        )
                        continue
                    if src1_port.num_modes != src2_port.num_modes:
                        warnings.warn(
                            f"Port pair {src1} and {src2} specified in 'port_symmetries' support "
                            f"different numbers of modes and will be ignored.",
                            stacklevel=3,
                        )
                        continue
                    pairs.append((src1, src2, src1_port.num_modes))
                element_mappings.extend(
                    (
                        ((src1, dst1), (src2, dst2), numpy.ones((src_modes, dst_modes)))
                        for src1, src2, src_modes in pairs
                        for dst1, dst2, dst_modes in pairs
                        if (src1, dst1) != (src2, dst2)
                    )
                )

            elif (
                len(port_symmetry) == 3
                and isinstance(port_symmetry[0], str)
                and isinstance(port_symmetry[1], str)
                and isinstance(port_symmetry[2], dict)
            ):
                # _ExplictMap
                src1, src2, maps = port_symmetry
                if src1 == src2:
                    continue
                src1_port = ports.get(src1)
                src2_port = ports.get(src2)
                if src1_port is None or src2_port is None:
                    missing_port = src1 if src1_port is None else src2
                    warnings.warn(
                        f"Port {missing_port} specified in 'port_symmetries' does not exist in "
                        f"component {component_name} or is defined for a different frequency "
                        f"range.",
                        stacklevel=3,
                    )
                    continue
                src_modes = src1_port.num_modes
                if src_modes != src2_port.num_modes:
                    warnings.warn(
                        f"Port pair {src1} and {src2} specified in 'port_symmetries' support "
                        f"different numbers of modes and will be ignored.",
                        stacklevel=3,
                    )
                    continue
                element_mappings.append(
                    ((src1, src1), (src2, src2), numpy.ones((src_modes, src_modes)))
                )

                for dst1, dst1_port in ports.items():
                    dst2 = maps.get(dst1)
                    if dst2 is None:
                        continue
                    dst2_port = ports.get(dst2)
                    if dst2_port is None:
                        warnings.warn(
                            f"Port {dst2} specified in 'port_symmetries' does not exist in "
                            f"component {component_name} or is defined for a different frequency "
                            f"range.",
                            stacklevel=3,
                        )
                        continue
                    dst_modes = dst1_port.num_modes
                    if dst_modes != dst2_port.num_modes:
                        warnings.warn(
                            f"Port pair {dst1} and {dst2} specified in 'port_symmetries' support "
                            f"different numbers of modes and will be ignored.",
                            stacklevel=3,
                        )
                        continue
                    element_mappings.append(
                        ((src1, dst1), (src2, dst2), numpy.ones((src_modes, dst_modes)))
                    )

            elif (
                len(port_symmetry) == 3
                and isinstance(port_symmetry[0], (tuple, list))
                and len(port_symmetry[0]) == 2
                and isinstance(port_symmetry[1], (tuple, list))
                and len(port_symmetry[1]) == 2
                and all(isinstance(x, str) for p in port_symmetry[:2] for x in p)
            ):
                # _PerElementMap
                (src1, dst1), (src2, dst2), factor = port_symmetry
                if (src1, dst1) == (src2, dst2):
                    continue

                src1_port = ports.get(src1)
                src2_port = ports.get(src2)
                dst1_port = ports.get(dst1)
                dst2_port = ports.get(dst2)
                if src1_port is None or src2_port is None or dst1_port is None or dst2_port is None:
                    missing_port = (
                        src1
                        if src1_port is None
                        else (src2 if src2_port is None else (dst1 if dst1_port is None else dst2))
                    )
                    warnings.warn(
                        f"Port {missing_port} specified in 'port_symmetries' does not exist in "
                        f"component {component_name} or is defined for a different frequency "
                        f"range.",
                        stacklevel=3,
                    )
                    continue
                if src1_port.num_modes != src2_port.num_modes:
                    warnings.warn(
                        f"Port pair {src1} and {src2} specified in 'port_symmetries' support "
                        f"different numbers of modes and will be ignored.",
                        stacklevel=3,
                    )
                    continue
                if dst1_port.num_modes != dst2_port.num_modes:
                    warnings.warn(
                        f"Port pair {dst1} and {dst2} specified in 'port_symmetries' support "
                        f"different numbers of modes and will be ignored.",
                        stacklevel=3,
                    )
                    continue
                shape = src1_port.num_modes, dst1_port.num_modes
                if numpy.ndim(factor) == 0:
                    factor = numpy.full(shape, factor)
                else:
                    factor = numpy.array(factor)
                    if factor.shape != shape:
                        warnings.warn(
                            f"Mapping ({src1}, {dst1}) to ({src2}, {dst2}) in 'port_symmetries' "
                            f"requires factor shape {shape}. Found {factor.shape}.",
                            stacklevel=3,
                        )
                        continue
                element_mappings.append(((src1, dst1), (src2, dst2), factor))

            else:
                warnings.warn(
                    f"Port symmetry specification {port_symmetry!r} does not match any of the "
                    f"required formats and will be ignored. Accepted formats are 'tuple[str]', "
                    f"'tuple[str, str, dict[str, str]]', and "
                    f"'tuple[tuple[str, str], tuple[str, str], complex | ndarray]'.",
                    stacklevel=3,
                )

        # Rank source ports by likelihood of being a source for most mappings and being less likely
        # to be a mapped source
        ranked = sorted(
            port_names,
            key=lambda p: (
                len([x for x in element_mappings if x[0][0] == p])
                - len([x for x in element_mappings if x[1][0] == p]),
                p,
            ),
        )

        retry = False
        required_sources = set(port_names)
        required_by_mapping = set()

        # Start looking for mapped sources from the most likely
        for src in reversed(ranked):
            if src in required_by_mapping:
                continue
            mapped = {}
            for (src1, _), (src2, dst2), _ in element_mappings:
                if src2 == src and src1 != src:
                    mapped[src1] = mapped.get(src1, set())
                    mapped[src1].add(dst2)

            # Look for a single source that can be used to map this src port using the rank
            src_options = [x for x in ranked if x in required_by_mapping]
            src_options.extend(x for x in ranked if x in mapped and x not in src_options)
            for required_src in src_options:
                if required_src in mapped and len(mapped[required_src]) == len(port_names):
                    required_sources.remove(src)
                    required_by_mapping.add(required_src)
                    break
            else:
                # We may be able to map this port using multiple sources, but let's
                # finish other options before using this wasteful alternative
                retry = retry or len(set().union(*mapped.values())) == len(port_names)

        if retry:
            for src in reversed(ranked):
                if src in required_by_mapping:
                    continue
                mapped = {}
                for (src1, _), (src2, dst2), _ in element_mappings:
                    if src2 == src and src1 != src:
                        mapped[src1] = mapped.get(src1, set())
                        mapped[src1].add(dst2)
                if len(set().union(*mapped.values())) == len(port_names):
                    required_sources.remove(src)
                    required_by_mapping.update(mapped.keys())

        return required_sources, element_mappings

    def get_simulations(
        self, component: Component, frequencies: Sequence[float], sources: Sequence[str] = ()
    ) -> dict[str, tidy3d.Simulation] | tidy3d.Simulation:
        """Return all simulations required by this component.

        Args:
            component: Instance of Component for calculation.
            frequencies: Sequence of frequencies for the simulation.
            sources: Port names to be used as sources (``{port}@{mode}``
              specifications are also accepted). If empty, use all required
              sources based on this model's port symmetries.

        Returns:
            Dictionary of ``tidy3d.Simulation`` indexed by source name or
            a single simulation if the component has no ports.
        """
        defaults = config.default_kwargs.get("tidy3d", {})

        frequencies = numpy.array(frequencies, dtype=float, ndmin=1)
        fmin = frequencies.min()
        fmax = frequencies.max()
        fmed = 0.5 * (fmin + fmax)
        max_wavelength = C_0 / fmin
        min_wavelength = C_0 / fmax

        classification = frequency_classification(frequencies)
        medium = (
            component.technology.get_background_medium(classification)
            if self.medium is None
            else self.medium
        )
        # NOTE: Workaround for Simulation not accepting MultiPhysicsMedium
        # TODO: Remove this once support is there.
        if isinstance(medium, tidy3d.MultiPhysicsMedium):
            medium = medium.optical
        use_angle_rotation = _isotropic_uniform(component.technology, classification)

        layer_refinement = _layer_steps_from_refinement(config.default_mesh_refinement)
        if isinstance(self.grid_spec, tidy3d.GridSpec):
            grid_spec = self.grid_spec
            mesh_refinement = config.default_mesh_refinement
        else:
            mesh_refinement = (
                config.default_mesh_refinement if self.grid_spec is None else self.grid_spec
            )
            layer_refinement = _layer_steps_from_refinement(mesh_refinement)
            grid_spec = tidy3d.GridSpec.auto(
                wavelength=min_wavelength,
                min_steps_per_wvl=mesh_refinement,
                min_steps_per_sim_size=mesh_refinement,
            )

        extrusion_tolerance = 0
        if isinstance(grid_spec.grid_z, tidy3d.AutoGrid):
            extrusion_specs = component.technology.extrusion_specs
            if classification == "optical":
                grid_lda = min_wavelength if grid_spec.wavelength is None else grid_spec.wavelength
                temp_structures = [
                    tidy3d.Structure(
                        geometry=tidy3d.Box(size=(1, 1, 1)), medium=spec.get_medium(classification)
                    )
                    for spec in extrusion_specs
                ]
                temp_scene = tidy3d.Scene(medium=medium, structures=temp_structures)
                _, eps_max = temp_scene.eps_bounds(fmed)
                extrusion_tolerance = grid_lda / (grid_spec.grid_z.min_steps_per_wvl * eps_max**0.5)
            elif len(extrusion_specs) > 0:
                for spec in component.technology.extrusion_specs:
                    t = spec.limits[1] - spec.limits[0]
                    if t > 0 and (extrusion_tolerance == 0 or extrusion_tolerance > t):
                        extrusion_tolerance = t
                extrusion_tolerance = max(config.tolerance, extrusion_tolerance / layer_refinement)
        elif isinstance(grid_spec.grid_z, tidy3d.components.grid.grid_spec.AbstractAutoGrid):
            extrusion_tolerance = grid_spec.grid_z._dl_min
        elif isinstance(grid_spec.grid_z, tidy3d.UniformGrid):
            extrusion_tolerance = grid_spec.grid_z.dl
        elif isinstance(grid_spec.grid_z, tidy3d.CustomGrid) and len(grid_spec.grid_z.dl) > 0:
            extrusion_tolerance = min(grid_spec.grid_z.dl)

        boundary_spec = (
            defaults.get(
                "boundary_spec",
                tidy3d.BoundarySpec.all_sides(boundary=tidy3d.Absorber(num_layers=70)),
            )
            if self.boundary_spec is None
            else self.boundary_spec
        )

        (xmin, ymin), (xmax, ymax) = component.bounds()
        max_bounds = max(xmax - xmin, ymax - ymin)

        component_ports = component.select_ports(classification)

        source_gap = defaults.get("source_gap", 0) if self.source_gap is None else self.source_gap
        if source_gap < 0:
            raise RuntimeError("'source_gap' cannot be negative.")

        if classification == "optical":
            pml_gap = (
                (0.6 * max_wavelength) if source_gap == 0 else (0.5 * max_wavelength + source_gap)
            )
            port_extension = 2 * pml_gap + max_bounds
        else:
            if source_gap == 0:
                source_gap = max_wavelength / 100
            grid_scale = max_bounds / mesh_refinement
            pml_gap = max(max_wavelength / 100, 3 * grid_scale) + source_gap
            port_extension = pml_gap + 200 * grid_scale

            if any(isinstance(p, Port) and p.bend_radius != 0 for p in component_ports.values()):
                warnings.warn(
                    "Electrical ports with non-zero bending radius can result in inaccurate mode "
                    "normalization, leading to invalid S matrices.",
                    stacklevel=2,
                )

        for port in component_ports.values():
            _, size, *_ = (
                port._axis_aligned_properties()
                if isinstance(port, (Port, FiberPort))
                else port._axis_aligned_properties(frequencies, 1.0)
            )
            port_extension = max(port_extension, size[0], size[1])

        # Bounds override
        delta = port_extension - 2 * pml_gap
        if self.bounds[0][0] is not None and self.bounds[0][0] < xmin - delta:
            port_extension = xmin - self.bounds[0][0] + 2 * pml_gap
        if self.bounds[0][1] is not None and self.bounds[0][1] < ymin - delta:
            port_extension = ymin - self.bounds[0][0] + 2 * pml_gap
        if self.bounds[1][0] is not None and self.bounds[1][0] > xmax - delta:
            port_extension = self.bounds[1][0] - xmax + 2 * pml_gap
        if self.bounds[1][1] is not None and self.bounds[1][1] > ymax - delta:
            port_extension = self.bounds[1][1] - ymax + 2 * pml_gap

        used_extrusions = []
        structures = [
            s.to_tidy3d()
            for s in component.extrude(
                port_extension,
                extrusion_tolerance=extrusion_tolerance,
                classification=classification,
                used_extrusions=used_extrusions,
            )
        ]

        # Sort to improve caching, but don't reorder different media
        i = 0
        while i < len(structures):
            current_medium = structures[i].medium
            j = i + 1
            while j < len(structures) and structures[j].medium == current_medium:
                j += 1
            # Even if j == i + 1 we want to sort internal geometries
            structures[i:j] = (
                tidy3d.Structure(geometry=geometry, medium=current_medium)
                for geometry in sorted(
                    [_inner_geometry_sort(s.geometry) for s in structures[i:j]], key=_geometry_key
                )
            )
            i = j

        port_structures = [
            structure
            for _, port in sorted(component_ports.items())
            if isinstance(port, FiberPort)
            for structure in port.to_tidy3d_structures()
        ]
        all_structures = structures + port_structures + list(self.structures)

        if len(sources) == 0:
            sources, _ = self._process_port_symmetries(component_ports, component.name)

        port_monitors = []
        port_sources = {}
        unused_sources = []
        grid_snapping_points = []
        for name, port in component_ports.items():
            if isinstance(port, (Port, FiberPort)):
                monitor = port.to_tidy3d_monitor(
                    frequencies, name=name, use_angle_rotation=use_angle_rotation
                )
                unused = True
                for mode_index in range(port.num_modes):
                    port_mode = f"{name}@{mode_index}"
                    if name in sources or port_mode in sources:
                        unused = False
                        port_sources[port_mode] = port.to_tidy3d_source(
                            frequencies,
                            mode_index=mode_index,
                            name=name,
                            use_angle_rotation=use_angle_rotation,
                        )
                if unused:
                    unused_sources.append(
                        port.to_tidy3d_source(
                            frequencies,
                            mode_index=0,
                            name=name,
                            use_angle_rotation=use_angle_rotation,
                        )
                    )

            else:
                epsilon_r = _get_epsilon(port.center, all_structures, medium, frequencies)
                monitor = port.to_tidy3d_monitor(frequencies, medium=epsilon_r, name=name)
                port_mode = f"{name}@0"
                if name in sources or port_mode in sources:
                    port_sources[port_mode] = port.to_tidy3d_source(
                        frequencies, medium=epsilon_r, name=name
                    )
                else:
                    unused_sources.append(
                        port.to_tidy3d_source(frequencies, medium=epsilon_r, name=name)
                    )

            port_monitors.append(monitor)

            i = monitor.size.index(0)
            p = [None, None, None]
            p[i] = monitor.center[i]
            grid_snapping_points.append(tuple(p))

        # Add layer refinements based on extruded layers and ports
        if classification == "electrical" and not isinstance(self.grid_spec, tidy3d.GridSpec):
            layer_refinement_specs = [
                _make_layer_refinement_spec(spec, layer_refinement, classification)
                for spec in sorted(
                    used_extrusions, key=lambda e: e.limits[1] - e.limits[0], reverse=True
                )
            ]
            grid_1d_update = {"max_scale": _auto_scale_from_refinement(mesh_refinement)}
            grid_spec = grid_spec.copy(
                update={
                    "snapping_points": grid_snapping_points,
                    "layer_refinement_specs": layer_refinement_specs,
                    "grid_x": grid_spec.grid_x.copy(update=grid_1d_update),
                    "grid_y": grid_spec.grid_y.copy(update=grid_1d_update),
                    "grid_z": grid_spec.grid_z.copy(update=grid_1d_update),
                }
            )

        # Simulation bounds
        zmin = 1e30
        zmax = -1e30
        for monitor in port_monitors:
            xmin = min(xmin, monitor.bounds[0][0])
            ymin = min(ymin, monitor.bounds[0][1])
            zmin = min(zmin, monitor.bounds[0][2])
            xmax = max(xmax, monitor.bounds[1][0])
            ymax = max(ymax, monitor.bounds[1][1])
            zmax = max(zmax, monitor.bounds[1][2])
        for s in structures:
            for i in range(2):
                lim = s.geometry.bounds[i][2]
                if -Z_MAX <= lim <= Z_MAX:
                    zmin = min(zmin, lim)
                    zmax = max(zmax, lim)
        if zmin > zmax:
            raise RuntimeError("No valid extrusion elements present in the component.")

        if isinstance(boundary_spec.x.minus, (tidy3d.PML, tidy3d.StablePML)):
            xmin -= pml_gap
        if isinstance(boundary_spec.x.plus, (tidy3d.PML, tidy3d.StablePML)):
            xmax += pml_gap
        if isinstance(boundary_spec.y.minus, (tidy3d.PML, tidy3d.StablePML)):
            ymin -= pml_gap
        if isinstance(boundary_spec.y.plus, (tidy3d.PML, tidy3d.StablePML)):
            ymax += pml_gap
        if isinstance(boundary_spec.z.minus, (tidy3d.PML, tidy3d.StablePML)):
            zmin -= pml_gap
        if isinstance(boundary_spec.z.plus, (tidy3d.PML, tidy3d.StablePML)):
            zmax += pml_gap

        bounds = numpy.array(((xmin, ymin, zmin), (xmax, ymax, zmax)))

        center = tuple(snap_to_grid(v) / 2 for v in bounds[0] + bounds[1])

        # Include margin for port sources
        size = tuple(snap_to_grid(v + pml_gap) for v in bounds[1] - bounds[0])

        bounding_box = tidy3d.Box(center=center, size=size)

        shutoff = defaults.get("shutoff", 1.0e-5) if self.shutoff is None else self.shutoff
        subpixel = defaults.get("subpixel", True) if self.subpixel is None else self.subpixel
        courant = defaults.get("courant", 0.99) if self.courant is None else self.courant

        base_simulation = tidy3d.Simulation(
            center=center,
            size=size,
            run_time=1e-12 if self.run_time is None else self.run_time,
            medium=medium,
            symmetry=(0, 0, 0),
            structures=[s for s in all_structures if bounding_box.intersects(s.geometry)],
            boundary_spec=boundary_spec,
            monitors=list(self.monitors) + port_monitors,
            grid_spec=grid_spec,
            shutoff=shutoff,
            subpixel=subpixel,
            courant=courant,
        )

        # Update keywords from base simulation
        update = {"symmetry": self.symmetry}

        if len(port_sources) == 0:
            return base_simulation.copy(update=update)

        # RunTimeSpec can only be used when sources are defined
        if self.run_time is None:
            update["run_time"] = defaults.get(
                "run_time", tidy3d.RunTimeSpec(quality_factor=5.0, source_factor=3.0)
            )

        # Use base grid to shift sources and update base simulation
        grid = base_simulation.grid

        delta_factor = 3 if source_gap == 0 else 2

        for name in port_sources:
            unused_source = port_sources[name]
            source = _source_shift(
                unused_source, grid, source_gap, component_ports[unused_source.name]
            )
            port_sources[name] = source

            # Make sure we have at least 2 grid cells between monitor and source
            i = source.size.index(0)
            p = [None, None, None]
            p[i] = source.center[i]
            grid_snapping_points.append(tuple(p))
            p[i] = (p[i] + unused_source.center[i]) / 2
            grid_snapping_points.append(tuple(p))

            delta = delta_factor * (xmin - source.bounds[0][0])
            if delta > 0:
                xmin -= delta
            delta = delta_factor * (source.bounds[1][0] - xmax)
            if delta > 0:
                xmax += delta

            delta = delta_factor * (ymin - source.bounds[0][1])
            if delta > 0:
                ymin -= delta
            delta = delta_factor * (source.bounds[1][1] - ymax)
            if delta > 0:
                ymax += delta

            delta = delta_factor * (zmin - source.bounds[0][2])
            if delta > 0:
                zmin -= delta
            delta = delta_factor * (source.bounds[1][2] - zmax)
            if delta > 0:
                zmax += delta

        for unused_source in unused_sources:
            source = _source_shift(
                unused_source, grid, source_gap, component_ports[unused_source.name]
            )

            # Make sure we have at least 2 grid cells between monitor and source
            i = source.size.index(0)
            p = [None, None, None]
            p[i] = source.center[i]
            grid_snapping_points.append(tuple(p))
            p[i] = (p[i] + unused_source.center[i]) / 2
            grid_snapping_points.append(tuple(p))

            delta = delta_factor * (xmin - source.bounds[0][0])
            if delta > 0:
                xmin -= delta
            delta = delta_factor * (source.bounds[1][0] - xmax)
            if delta > 0:
                xmax += delta

            delta = delta_factor * (ymin - source.bounds[0][1])
            if delta > 0:
                ymin -= delta
            delta = delta_factor * (source.bounds[1][1] - ymax)
            if delta > 0:
                ymax += delta

            delta = delta_factor * (zmin - source.bounds[0][2])
            if delta > 0:
                zmin -= delta
            delta = delta_factor * (source.bounds[1][2] - zmax)
            if delta > 0:
                zmax += delta

        if classification == "electrical" and not isinstance(self.grid_spec, tidy3d.GridSpec):
            update["grid_spec"] = grid_spec.copy(update={"snapping_points": grid_snapping_points})

        for monitor in port_monitors:
            if xmin >= monitor.bounds[0][0]:
                xmin -= config.grid
            if ymin >= monitor.bounds[0][1]:
                ymin -= config.grid
            if zmin >= monitor.bounds[0][2]:
                zmin -= config.grid
            if xmax <= monitor.bounds[1][0]:
                xmax += config.grid
            if ymax <= monitor.bounds[1][1]:
                ymax += config.grid
            if zmax <= monitor.bounds[1][2]:
                zmax += config.grid

        bounds = numpy.array(((xmin, ymin, zmin), (xmax, ymax, zmax)))

        # Bounds override
        for i in range(3):
            if self.bounds[0][i] is not None:
                bounds[0, i] = self.bounds[0][i]
            if self.bounds[1][i] is not None:
                bounds[1, i] = self.bounds[1][i]

        update["center"] = tuple(snap_to_grid(v) / 2 for v in bounds[0] + bounds[1])
        update["size"] = tuple(snap_to_grid(v) for v in bounds[1] - bounds[0])

        bounding_box = tidy3d.Box(center=update["center"], size=update["size"])

        update["structures"] = [s for s in all_structures if bounding_box.intersects(s.geometry)]

        if self.boundary_spec is None and any(s == 0 for s in size):
            axis = "yxz"[size.index(0)]
            update["boundary_spec"] = boundary_spec.copy(
                update={axis: tidy3d.Boundary(minus=tidy3d.Periodic(), plus=tidy3d.Periodic())}
            )

        # Only the first simulation will store mode field data, if necessary due to mode remaping
        mode_remap = _requires_mode_remap(
            tuple(self.symmetry),
            (mon for mon in port_monitors if isinstance(mon, tidy3d.ModeMonitor)),
        )
        if not mode_remap:
            update["monitors"] = list(self.monitors) + [
                mon.copy(update={"store_fields_direction": None})
                if isinstance(mon, tidy3d.ModeMonitor)
                else mon
                for mon in port_monitors
            ]

        simulations = {}
        for name in sorted(port_sources):
            update["sources"] = [port_sources[name]]
            simulations[name] = base_simulation.copy(update=update)
            if mode_remap:
                # Mode fields required only in 1 simulation
                mode_remap = False
                update["monitors"] = list(self.monitors) + [
                    mon.copy(update={"store_fields_direction": None})
                    if isinstance(mon, tidy3d.ModeMonitor)
                    else mon
                    for mon in port_monitors
                ]

        for key, value in self.simulation_updates.items():
            path = key.split("/")
            if "@" in path[0]:
                sim = simulations.get(path[0])
                if sim is not None:
                    simulations[path[0]] = _updated_tidy3d(sim, path[1:], value)
            else:
                simulations = {
                    name: _updated_tidy3d(sim, path, value) for name, sim in simulations.items()
                }

        return simulations

    @cache_s_matrix
    def start(
        self,
        component: Component,
        frequencies: Sequence[float],
        *,
        inputs: Sequence[str] = (),
        verbose: bool | None = None,
        cost_estimation: bool = False,
        **kwargs: Any,
    ) -> _Tidy3DModelRunner:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            inputs: Limit calculation to specific inputs. Each item must be
              a port name or a ``{port}@{mode}`` specification.
            verbose: If set, overrides the model's `verbose` attribute.
            cost_estimation: If set, simulations are uploaded, but not
              executed. S matrix will *not* be computed.
            **kwargs: Unused.

        Returns:
            Result object with attributes ``status`` and ``s_matrix``.

        Important:
            When using geometry symmetry, the mode numbering in ``inputs``
            is relative to the solver run *with the symmetry applied*, not
            the mode number presented in the final S matrix.
        """
        frequencies = numpy.array(frequencies, dtype=float, ndmin=1)
        classification = frequency_classification(frequencies)
        inputs = tuple(inputs)
        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        if verbose is None:
            verbose = self.verbose

        required_sources, element_mappings = self._process_port_symmetries(
            component_ports, component.name
        )
        if len(inputs) > 0:
            required_sources = inputs

        simulations = self.get_simulations(component, frequencies, required_sources)
        if not isinstance(simulations, dict):
            raise RuntimeError(
                f"Tidy3DModel found no source ports for {classification} frequencies. Please make "
                f"sure that component '{component.name}' has {classification} ports."
            )

        sim = next(iter(simulations.values()))
        port_epsilon = {
            name: _get_epsilon(port.center, sim.structures, sim.medium, frequencies)
            for name, port in component_ports.items()
            if not isinstance(port, Port)
        }

        folder_name = _filename_cleanup(component.name)
        if len(folder_name) == 0:
            folder_name = "default"

        return _Tidy3DModelRunner(
            frequencies=frequencies,
            simulations=simulations,
            ports=component_ports,
            port_epsilon=port_epsilon,
            element_mappings=element_mappings,
            folder_name=folder_name,
            data_path=self.data_path_for(component, _skip_warning=True),
            batch_file=self.batch_file_for(component, _skip_warning=True),
            cost_estimation=cost_estimation,
            verbose=verbose,
        )

    def batch_data(
        self,
        component: Component,
        frequencies: Sequence[float],
        *,
        inputs: Sequence[str] = (),
        verbose: bool | None = None,
        show_progress: bool = True,
        **kwargs: Any,
    ):
        """Return the Tidy3D BatchData for a given component.

        Uses the same arguments as :func:`Tidy3DModel.start`.
        """
        from tidy3d.web import BatchData  # noqa: PLC0415

        if verbose is None:
            verbose = self.verbose

        if show_progress:
            print("Starting…", end="\r", flush=True)

        runner = self.start(component, frequencies, inputs=inputs, verbose=verbose, **kwargs)

        progress_chars = "-\\|/"
        i = 0
        while True:
            status = runner.status
            message = status["message"]
            if message == "success":
                if show_progress:
                    print("Progress: 100% ", end="\n", flush=True)
                task_ids = {}
                task_paths = {}
                for k, r in runner.runners.items():
                    if isinstance(r, _Tidy3DTaskRunner):
                        task_paths[k] = str(r.data_file())
                        task_ids[k] = r.task_id or ""
                return BatchData(
                    task_ids=task_ids,
                    task_paths=task_paths,
                    verbose=verbose,
                    # cached_tasks=dict.fromkeys(task_paths, True),
                )
            elif message == "running":
                if show_progress:
                    p = max(0, min(100, int(status.get("progress", 0))))
                    c = progress_chars[i]
                    i = (i + 1) % len(progress_chars)
                    print(f"Progress: {p}% {c}", end="\r", flush=True)
                time.sleep(0.3)
            elif message == "error":
                if show_progress:
                    print("Progress: error", end="\n", flush=True)
                raise RuntimeError("Batch run resulted in error.")
            else:
                raise RuntimeError(f"Status message unknown: {message:r}.")

    def test_port_symmetries(
        self,
        component: Component,
        frequencies: Sequence[float],
        plot_error: bool = True,
        atol: float = 0.02,
        **kwargs: Any,
    ) -> bool:
        """
        Test this models port symmetries with a component.

        Effectively executes all simulations required without symmetries and
        compares with the symmetry setting.

        Args:
            component: Component to test.
            frequencies: Frequencies to use during the test.
            plot_error: Create a plot for elements with symmetry errors.
            atol: Absolute tolerance when comparing results.
            **kwargs: Arguments to replace in the model during the test.

        Returns:
            Boolean indicating whether the symmetries for all Tidy3D models in
            the component are correct.
        """
        success = True
        if len(self.port_symmetries) == 0:
            return True

        original_args = {k: getattr(self, k) for k in kwargs}
        for k, v in kwargs.items():
            setattr(self, k, v)

        port_symmetries = self.port_symmetries
        self.port_symmetries = []
        s1 = self.s_matrix(component, frequencies)
        self.port_symmetries = port_symmetries
        s0 = self.s_matrix(component, frequencies)

        for k, v in original_args.items():
            setattr(self, k, v)

        ax = None
        for k in s0.elements:
            if not numpy.allclose(s0[k], s1[k], atol=atol):
                success = False
                if plot_error and ax is None:
                    try:
                        from matplotlib import pyplot  # noqa: PLC0415

                        _, ax = pyplot.subplots(2, 2, figsize=(10, 6), tight_layout=True)
                    except ImportError:
                        pass
                if ax is not None:
                    ax[0, 0].plot(frequencies, numpy.real(s0[k]), label=str(k) + " (sym)")
                    ax[0, 1].plot(frequencies, numpy.imag(s0[k]), label=str(k) + " (sym)")
                    ax[1, 0].plot(frequencies, numpy.real(s1[k]), label=str(k))
                    ax[1, 1].plot(frequencies, numpy.imag(s1[k]), label=str(k))
        if ax is not None:
            ax[0, 0].set(xlabel="Frequency (Hz)", ylabel="Real part")
            ax[0, 1].set(xlabel="Frequency (Hz)", ylabel="Imaginary part")
            ax[1, 0].set(xlabel="Frequency (Hz)", ylabel="Real part")
            ax[1, 1].set(xlabel="Frequency (Hz)", ylabel="Imaginary part")
            for a in ax.flat:
                a.legend()
        return success

    # Deprecated: kept for backwards compatibility with old phf files
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "Tidy3DModel":
        """De-serialize this model."""
        version = byte_repr[0]
        if version == 1:
            obj = dict(_from_bytes(byte_repr[1:]))

        elif version == 0:
            n_size = struct.calcsize("<BL")
            n = struct.unpack("<L", byte_repr[1:n_size])[0]
            cursor = struct.calcsize("<BL" + n * "Q")
            lengths = struct.unpack("<" + n * "Q", byte_repr[n_size:cursor])

            obj = json.loads(byte_repr[cursor : cursor + lengths[0]].decode("utf-8"))
            cursor += lengths[0]

            models = [None] * (n - 1)
            for i, length in enumerate(lengths[1:]):
                models[i] = _tidy3d_from_bytes(byte_repr[cursor : cursor + length])
                cursor += length

            if cursor != len(byte_repr):
                raise RuntimeError("Invalid byte representation for Tidy3DModel.")

            indices = obj.pop("_tidy3d_indices_")
            for name, (i, j) in indices.items():
                if j < 0:
                    obj[name] = models[i]
                else:
                    obj[name] = [models[m] for m in range(i, j)]

        # zlib-compressed json used before versioning
        elif version == 0x78:
            obj = json.loads(zlib.decompress(byte_repr).decode("utf-8"))
            obj = _decode_arrays(obj)

            item = obj.get("medium")
            if isinstance(item, dict):
                obj["medium"] = pydantic.v1.parse_obj_as(
                    tidy3d.components.medium.MediumType3D,
                    obj["medium"],
                    type_name=obj["medium"]["type"],
                )

            item = obj.get("boundary_spec")
            if isinstance(item, dict):
                obj["boundary_spec"] = pydantic.v1.parse_obj_as(
                    tidy3d.BoundarySpec, item, type_name=item["type"]
                )

            item = obj.get("run_time")
            if isinstance(item, dict):
                obj["run_time"] = pydantic.v1.parse_obj_as(
                    tidy3d.RunTimeSpec, item, type_name=item["type"]
                )

            item = obj.get("grid_spec")
            if isinstance(item, dict):
                obj["grid_spec"] = pydantic.v1.parse_obj_as(
                    tidy3d.GridSpec, item, type_name=item["type"]
                )

            obj["monitors"] = [
                pydantic.v1.parse_obj_as(
                    tidy3d.components.monitor.MonitorType, mon, type_name=mon["type"]
                )
                for mon in obj.get("monitors", ())
            ]

            obj["structures"] = [
                pydantic.v1.parse_obj_as(tidy3d.Structure, s, type_name=s["type"])
                for s in obj.get("structures", ())
            ]
        else:
            raise RuntimeError(
                f"Unsupported version found in Tidy3DModel byte representation: {version}."
            )

        return cls(**obj)


# Note: Kept for backwards compatibility. Do not use: horrible performance.
def _convert_arrays(obj: Any) -> Any:
    if isinstance(obj, numpy.ndarray):
        return obj.tolist()
    if isinstance(obj, xarray.Dataset):
        return {"PhotonForge xarray.Dataset": obj.to_dict()}
    if isinstance(obj, xarray.DataArray):
        return {"PhotonForge xarray.DataArray": obj.to_dict()}
    if isinstance(obj, dict):
        return {k: _convert_arrays(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_arrays(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_convert_arrays(x) for x in obj)
    if isinstance(obj, set):
        return {_convert_arrays(x) for x in obj}
    return obj


# Note: Kept for backwards compatibility. Do not use: horrible performance.
def _decode_arrays(obj: Any) -> Any:
    if isinstance(obj, dict):
        if len(obj) == 1:
            k, v = next(iter(obj.items()))
            if k == "PhotonForge xarray.Dataset":
                return xarray.Dataset.from_dict(v)
            if k == "PhotonForge xarray.DataArray":
                return xarray.DataArray.from_dict(v)
        return {k: _decode_arrays(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_arrays(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_decode_arrays(x) for x in obj)
    if isinstance(obj, set):
        return {_decode_arrays(x) for x in obj}
    return obj


register_model_class(Tidy3DModel)
