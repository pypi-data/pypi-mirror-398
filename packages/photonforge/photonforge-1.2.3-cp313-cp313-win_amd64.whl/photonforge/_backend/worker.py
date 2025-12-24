import logging
import os
import pathlib
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import QueueHandler
from multiprocessing import Queue, SimpleQueue, current_process
from threading import Event, Lock, Thread
from typing import Any
from uuid import UUID, uuid5

import numpy as np
from tidy3d import Medium
from tidy3d.web.api.webapi import abort
from tidy3d.web.core.exceptions import WebError

import photonforge as pf
from photonforge._backend import default_project
from photonforge._backend.component import component_to_node
from photonforge._backend.netlist import netlist_to_component
from photonforge._backend.types import (
    JobStatus,
    ProjectId,
    SMatrix,
    SMatrixElement,
    TimeSeries,
    TimeSeriesElement,
)

logger = logging.getLogger(f"photonforge.server.worker.{current_process().name}")


project = None
assets = {}


def init_pda(project_name):
    global assets, logger
    assets = {}

    namespace = UUID("c6ef3ed0-c932-49a4-9520-a97bb76ca96c")

    pf.config.default_technology = pf.Technology("Empty", "0", {}, [], {}, Medium())

    libs = []
    components = []
    for name in dir(default_project):
        if name.startswith("_"):
            continue
        c = getattr(default_project, name)()
        c._id = str(uuid5(namespace, name))
        assets[c._id] = c
        components.append(c)
    components.sort(key=lambda c: c.name)
    libs.append(("Analytical Components", components))

    try:
        import siepic_forge as siepic  # noqa: PLC0415
    except ModuleNotFoundError:
        logger.warn("Module siepic-forge not found")
        siepic = None

    if siepic is not None:
        tech = siepic.ebeam()
        components = []
        for name in siepic.component_names:
            c = siepic.component(name, tech)
            c._id = str(uuid5(namespace, name + tech.name + tech.version))
            assets[c._id] = c
            components.append(c)
        components.sort(key=lambda c: c.name)
        libs.append((tech.name, components))

    try:
        import luxtelligence_lnoi400_forge as lxt  # noqa: PLC0415
    except ModuleNotFoundError:
        logger.warn("Module luxtelligence-lnoi400-forge not found")
        lxt = None

    if lxt is not None:
        tech = lxt.lnoi400()
        tech.ports["RWG1000"].num_modes = 1  # Make default components compatible with Siepic
        components = []
        for name in lxt.component_names:
            c = getattr(lxt.component, name)(technology=tech)
            c._id = str(uuid5(namespace, name + tech.name + tech.version))
            assets[c._id] = c
            components.append(c)
        components.sort(key=lambda c: c.name)
        libs.append((tech.name, components))

    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        import custom_components as cc  # noqa: PLC0415

        logger.debug(f"Custom components found: {cc}")
    except ModuleNotFoundError:
        logger.debug(f"Custom components not found in path: {', '.join(sys.path)}")
        cc = None

    if cc is not None:
        components = []
        component_names = []

        if hasattr(cc, "component_names"):
            try:
                component_names = [name for name in cc.component_names if isinstance(name, str)]
            except Exception as err:
                logger.error(f"Error inspecting 'custom_components.component_names': {err}")

        for name in dir(cc):
            if name.startswith("_"):
                continue
            c = getattr(cc, name)
            if isinstance(c, pf.Component):
                c._id = str(uuid5(namespace, name + c.technology.name + c.technology.version))
                assets[c._id] = c
                components.append(c)
            elif callable(c) and (
                name in component_names
                or "custom_components." + name in pf.extension._component_registry
            ):
                try:
                    c = c()
                    c._id = str(uuid5(namespace, name + c.technology.name + c.technology.version))
                    assets[c._id] = c
                    components.append(c)
                except Exception as err:
                    logger.error(f"Error creating component from {name!r}: {err}")

        components.sort(key=lambda c: c.name)
        libs.append(("Custom", components))

    return libs


def from_pda(asset_id: str | UUID):
    global assets, logger
    return assets.get(str(asset_id))


def to_pda(asset):
    global project, assets, logger
    # project.save_component(asset)
    assets[asset._id] = asset


def monitor_status(runner, job_status, status_updates, tasks, lock, terminate, progress_factor):
    last_status = None
    message = "running"
    while message == "running":
        time.sleep(0.8)

        if terminate.is_set():
            job_status.state = "failed"
            job_status.error = "Job terminated"
            status_updates.put(job_status)
            logger.info(f"Monitor for job {job_status.id} terminated")
            return "terminated"

        try:
            status = runner.status
            message = status["message"]
        except Exception as err:
            job_status.state = "failed"
            job_status.error = str(err)
            status_updates.put(job_status)
            logger.error(f"Job {job_status.id} error: {job_status.error}")
            return "failed"

        with lock:
            tasks.update(status.get("tasks", {}))

        if last_status is None:
            job_status.state = "running"
            job_status.startedAt = datetime.now()

        if status != last_status:
            logger.debug(f"Job {job_status.id}  status: {status}")
            last_status = status
            job_status.progress = min(100, max(0, int(progress_factor * status["progress"])))
            status_updates.put(job_status)

    return message


def monitor_time_stepping(
    stepper, runner, time_step, steps, job_status, status_updates, tasks, lock, terminate
):
    message = monitor_status(runner, job_status, status_updates, tasks, lock, terminate, 0.5)
    if message != "success":
        job_status.state = "failed"
        if job_status.error is None:
            job_status.error = "Time stepper setup failed: {message}"
            status_updates.put(job_status)
            logger.error(f"Job {job_status.id} error: {job_status.error}")
        return

    with lock:
        tasks.clear()

    outputs = {}
    for step in range(steps):
        try:
            output = stepper.step_single({}, step, True, step == steps - 1)
            for k, v in output.items():
                if k not in outputs:
                    outputs[k] = np.zeros(steps, dtype=complex)
                outputs[k][step] = v
        except Exception as err:
            job_status.state = "failed"
            job_status.error = str(err)
            status_updates.put(job_status)
            logger.error(f"Job {job_status.id} error: {job_status.error}")
            return

        progress = 50 + int(50 * (step + 1) / steps)
        if progress > job_status.progress + 1:
            job_status.progress = progress
            status_updates.put(job_status)
            logger.debug(f"Job {job_status.id}  status: {job_status}")

    # TODO: Should we always save in PDA store or have a specific flag to indicate this?
    to_pda(pf.TimeSeries(outputs, time_step, 0))

    logger.info(f"Time stepper for job {job_status.id} succeeded")

    job_status.completedAt = datetime.now()
    job_status.state = "succeeded"
    job_status.progress = 100
    job_status.result = TimeSeries(
        timeStep=time_step,
        timeIndex=0,
        numSteps=steps,
        elements=[
            TimeSeriesElement(name=k, values=[(z.real, z.imag) for z in v])
            for k, v in outputs.items()
        ],
    )
    status_updates.put(job_status)


def monitor_s_matrix(runner, job_status, status_updates, tasks, lock, terminate):
    if isinstance(runner, SMatrix):
        message = "success"
    else:
        message = monitor_status(runner, job_status, status_updates, tasks, lock, terminate, 1)
    job_status.completedAt = datetime.now()

    if message == "success":
        job_status.state = "succeeded"
        logger.info(f"S matrix runner for job {job_status.id} succeeded")

        with lock:
            tasks.clear()

        try:
            s_matrix = runner if isinstance(runner, SMatrix) else runner.s_matrix
        except Exception as err:
            job_status.state = "failed"
            job_status.error = str(err)
            status_updates.put(job_status)
            logger.error(f"Job {job_status.id} error: {job_status.error}")
            return

        if s_matrix is not None:
            logger.debug(f"S matrix for job {job_status.id}: {s_matrix}")

            # TODO: Should we always save in PDA store or have a specific flag to indicate this?
            to_pda(s_matrix)

            elements = [
                SMatrixElement(input=i, output=j, values=[(z.real, z.imag) for z in v.tolist()])
                for (i, j), v in s_matrix.elements.items()
            ]
            result = SMatrix(
                frequencies=s_matrix.frequencies,
                wavelengths=s_matrix.wavelengths,
                elements=elements,
            )
            job_status.result = result
    else:
        job_status.state = "failed"
        if job_status.error is None:
            job_status.error = "S matrix computation failed: {message}"
            status_updates.put(job_status)
            logger.error(f"Job {job_status.id} error: {job_status.error}")

    status_updates.put(job_status)


@dataclass
class Job:
    status: JobStatus
    tasks: dict[str, Any]
    lock: Lock
    terminate: Event
    thread: Thread = None


def start_worker(
    project_id: ProjectId,
    work_queue: SimpleQueue,
    response_queue: SimpleQueue,
    status_updates: SimpleQueue,
    log_queue: Queue,
):
    global project, assets, logger

    logger.addHandler(QueueHandler(log_queue))
    logger.debug("Worker started.")

    # TODO: use correct project
    project_name = str(project_id)
    libs = init_pda(project_name)

    jobs: dict[str, Job] = {}

    while True:
        if work_queue.empty():
            time.sleep(0.5)
            continue

        item = work_queue.get()

        if item == "terminate":
            logger.debug("Terminating worker.")
            for job_id, job in jobs.items():
                logger.info(f"Aborting job {job_id}")
                job.terminate.set()

            for job_id, job in jobs.items():
                if job.thread is None:
                    continue
                logger.debug(f"Joining job {job_id} thread")
                job.thread.join()
                for task_id in job.tasks:
                    logger.info(f"Aborting task {task_id}")
                    try:
                        abort(task_id)
                    except WebError:
                        pass

            return

        elif item[0] == "abort":
            job_id, reason = item[1:]

            job = jobs.get(job_id)
            if job is None:
                continue

            logger.info(f"Aborting job {job_id}")
            job.terminate.set()
            job.thread.join()

            if job.status in ("succeeded", "failed", "aborted"):
                continue

            job.status.completedAt = datetime.now()
            job.status.reason = reason
            job.status.state = "aborted"
            status_updates.put(job.status)

            remaining_tasks = set()
            for other_id, other_job in jobs.items():
                if other_id != job_id:
                    with other_job.lock:
                        remaining_tasks.update(other_job.tasks.keys())
            for task_id in job.tasks:
                if task_id in remaining_tasks:
                    logger.debug(f"Skipping task {task_id}")
                    continue
                logger.info(f"Aborting task {task_id}")
                try:
                    abort(task_id)
                except WebError:
                    pass
            job.tasks = {}

        elif item[0] == "components":
            for name, components in libs:
                logger.debug(f"Processing components from {name!r}")
                if len(components) == 0:
                    continue
                response_queue.put(name)
                for component in components:
                    try:
                        node = component_to_node(component)
                        logger.debug(f"Converted {component._id}: {component.name!r}")
                    except Exception as err:
                        logger.error(f"Error converting component {component._id}: {err}")
                        continue
                    response_queue.put(node)
            response_queue.put(None)

        elif item[0] == "export":
            request = item[1]
            logger.info(f"Exporting netlist from application {request.applicationId}")

            try:
                component = netlist_to_component(request.netlist)
            except Exception as err:
                response_queue.put((False, f"Error parsing netlist: {err}"))
                logger.error(
                    f"Error parsing netlist for application {request.applicationId}: {err}"
                )
                continue

            try:
                fd, path = tempfile.mkstemp(".phf")
                logger.debug(f"Using path {path!r} for conversion ({request.applicationId})")
                os.close(fd)
                pf.write_phf(path, component)
            except Exception as err:
                pathlib.Path(path).unlink(True)
                response_queue.put((False, f"Error creating phf file: {err}"))
                logger.error(f"Error creating phf file for job {request.applicationId}: {err}")
                continue

            response_queue.put((True, path))

        else:
            # Create a new job
            request, job_status = item
            logger.info(f"Creating job {job_status.id}")

            job = Job(status=job_status, tasks={}, lock=Lock(), terminate=Event())
            jobs[job_status.id] = job

            try:
                component = netlist_to_component(request.netlist)
            except Exception as err:
                job_status.state = "failed"
                job_status.error = f"Error parsing netlist: {err}"
                logger.error(f"Error parsing netlist for job {job_status.id}: {err}")
                status_updates.put(job_status)
                continue

            # TODO: Should we always save in PDA store or have a specific flag to indicate this?
            to_pda(component)

            if request.simulationSettings.simulationMode == "time":
                logger.info(f"Starting time-domain simulation for job {job_status.id}")
                settings = request.simulationSettings.timeDomain
                if settings is None:
                    job_status.state = "failed"
                    job_status.error = "Missing frequency domain simulation settings"
                    logger.error(f"Missing frequency domain settings for job {job_status.id}")
                    status_updates.put(job_status)
                    continue

                time_step = settings.timeStep
                steps = int(settings.duration // time_step)
                carrier_frequency = settings.carrierFrequency

                if carrier_frequency == 0:
                    start_freq = 0
                    end_freq = settings.frequencyBandwidth * 2
                else:
                    start_freq = max(0, carrier_frequency - settings.frequencyBandwidth)
                    end_freq = carrier_frequency + settings.frequencyBandwidth
                frequencies = np.linspace(start_freq, end_freq, settings.frequencyPoints)

                monitors = {}
                for monitor in settings.monitors:
                    for reference in component.references:
                        if reference._id == str(monitor.nodeId):
                            monitors[monitor.name] = reference[monitor.portName]
                            break
                    if monitor.name not in monitors:
                        logger.warning(f"Invalid monitor in job {job_status.id}: {monitor}")

                classification = pf.frequency_classification(frequencies)
                model = component.select_active_model(classification)
                if model is None:
                    job_status.state = "failed"
                    job_status.error = (
                        f"No model for {classification} frequencies in component ID "
                        f"'{component._id}'."
                    )
                    logger.error(
                        f"No model for {classification} frequencies in component ID "
                        f"'{component._id}' (job {job_status.id})"
                    )
                    status_updates.put(job_status)
                    continue

                stepper = model.time_stepper
                if stepper is None:
                    job_status.state = "failed"
                    job_status.error = (
                        f"No time stepper for {model} in component ID '{component._id}'.",
                    )
                    logger.error(
                        f"No time stepper for {model} in component ID '{component._id}' "
                        f"(job {job_status.id})"
                    )
                    status_updates.put(job_status)
                    continue

                try:
                    runner = stepper.setup_state(
                        component=component,
                        time_step=time_step,
                        carrier_frequency=carrier_frequency,
                        frequencies=frequencies,
                        monitors=monitors,
                        show_progress=False,
                    )
                except Exception as err:
                    job_status.state = "failed"
                    job_status.error = f"Time stepper setup error: {err}"
                    logger.error(f"Time stepper setup error for job {job_status.id}: {err}")
                    status_updates.put(job_status)
                    continue

                job.thread = Thread(
                    target=monitor_time_stepping,
                    args=(
                        stepper,
                        runner,
                        time_step,
                        steps,
                        job.status,
                        status_updates,
                        job.tasks,
                        job.lock,
                        job.terminate,
                    ),
                    name=f"T_{job_status.id}",
                    daemon=True,
                )
                job.thread.start()
                logger.debug(f"Started monitor thread for job {job_status.id}")

            else:
                logger.info(f"Starting frequency-domain simulation for job {job_status.id}")
                if request.simulationSettings.frequencyDomain is None:
                    job_status.state = "failed"
                    job_status.error = "Missing frequency domain simulation settings"
                    logger.error(f"Missing frequency domain settings for job {job_status.id}")
                    status_updates.put(job_status)
                    continue

                try:
                    lda_range = request.simulationSettings.frequencyDomain.wavelength
                    frequencies = pf.C_0 / np.linspace(
                        lda_range.start, lda_range.stop, lda_range.points
                    )
                    classification = pf.frequency_classification(frequencies)
                except Exception as err:
                    job_status.state = "failed"
                    job_status.error = f"Error in wavelength setting: {err}"
                    logger.error(f"Error in wavelength setting for job {job_status.id}: {err}")
                    status_updates.put(job_status)
                    continue

                model = component.select_active_model(classification)
                if model is None:
                    job_status.state = "failed"
                    job_status.error = (
                        f"No model for {classification} frequencies in component ID "
                        f"'{component._id}'.",
                    )
                    logger.error(
                        f"No model for {classification} frequencies in component ID "
                        f"'{component._id}' (job {job_status.id})"
                    )
                    status_updates.put(job_status)
                    continue

                try:
                    runner = model.start(component, frequencies, verbose=False)
                except Exception as err:
                    job_status.state = "failed"
                    job_status.error = f"Error starting simulation model: {err}"
                    logger.error(f"Error starting simulation for job {job_status.id}: {err}")
                    status_updates.put(job_status)
                    continue

                job.thread = Thread(
                    target=monitor_s_matrix,
                    args=(runner, job.status, status_updates, job.tasks, job.lock, job.terminate),
                    name=f"T_{job_status.id}",
                    daemon=True,
                )
                job.thread.start()
                logger.debug(f"Started monitor thread for job {job_status.id}")


if __name__ == "__main__":
    from multiprocessing import Process

    logging.basicConfig(
        level="DEBUG", format="%(levelname)-8s %(processName)s:%(threadName)s: %(message)s"
    )
    logging.getLogger("httpx").setLevel("WARNING")
    logging.getLogger("httpcore").setLevel("WARNING")

    work_queue = SimpleQueue()
    response_queue = SimpleQueue()
    status_queue = SimpleQueue()
    log_queue = Queue()

    worker = Process(
        target=start_worker,
        args=("PROJECT_ID", work_queue, response_queue, status_queue, log_queue),
        name="TEST_WORKER",
        daemon=True,
    )
    worker.start()
    work_queue.put(("components", None))

    while True:
        while response_queue.empty():
            time.sleep(0.1)
        if response_queue.get() is None:
            break

    work_queue.put("terminate")
    worker.join()
