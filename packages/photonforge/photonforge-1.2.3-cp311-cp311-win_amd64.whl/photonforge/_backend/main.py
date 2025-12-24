import asyncio
import logging
import logging.config
import time
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from datetime import datetime
from logging.handlers import QueueHandler
from multiprocessing import Process, Queue, SimpleQueue
from pathlib import Path
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from photonforge._backend.types import (
    ApplicationId,
    JobId,
    JobStatus,
    Netlist,
    Node,
    ProjectId,
    SimulationSettings,
)
from photonforge._backend.worker import start_worker
from photonforge.extension import __version__


class NetlistExportRequest(BaseModel):
    projectId: ProjectId
    applicationId: ApplicationId
    netlist: Netlist
    documentHeads: list[str] | None = None


class JobSubmissionRequest(BaseModel):
    projectId: ProjectId
    applicationId: ApplicationId
    netlist: Netlist
    simulationSettings: SimulationSettings
    documentHeads: list[str] | None = None


class JobAbortRequest(BaseModel):
    reason: str | None = None


class Library(BaseModel):
    name: str
    components: list[Node]


class LibrariesResponse(BaseModel):
    libraries: list[Library]


async def log_handler(log_queue):
    logger = logging.getLogger("photonforge.server")
    while True:
        if log_queue.empty():
            await asyncio.sleep(0.1)
            continue
        record = log_queue.get()
        if record is None:
            break
        logger.handle(record)


async def monitor_status(status_queue, jobs, lock):
    while True:
        if status_queue.empty():
            await asyncio.sleep(0.1)
            continue
        job_status = status_queue.get()
        if job_status is None:
            break
        async with lock:
            jobs[job_status.id] = job_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.log_queue = Queue()
    app.state.logger = logging.getLogger("photonforge.server.queue")
    app.state.logger.addHandler(QueueHandler(app.state.log_queue))

    log_handler_task = asyncio.create_task(log_handler(app.state.log_queue), name="Log handler")

    app.state.workers: dict[ProjectId, tuple[Process, SimpleQueue, SimpleQueue]] = {}
    app.state.jobs_lock = asyncio.Lock()
    app.state.jobs: dict[JobId, JobStatus] = {}
    app.state.status_queue = SimpleQueue()

    app.state.logger.debug("Creating status monitor task")
    monitor_status_task = asyncio.create_task(
        monitor_status(app.state.status_queue, app.state.jobs, app.state.jobs_lock),
        name="Status monitor",
    )

    yield

    app.state.logger.info("Shuting down workers")

    for project_id, (worker, work_queue, _) in app.state.workers.items():
        app.state.logger.debug(f"Terminating worker {project_id}")
        if worker.is_alive():
            work_queue.put("terminate")

    for project_id, (worker, _, _) in app.state.workers.items():
        app.state.logger.debug(f"Closing worker {project_id}")
        worker.join()
        worker.close()

    app.state.logger.info("Shuting down logging and status monitor tasks")

    app.state.status_queue.put(None)
    app.state.log_queue.put(None)
    await monitor_status_task
    await log_handler_task


app = FastAPI(
    title="PhotonForge Server",
    description="PhotonForge local server for GUI interaction.",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://photonforge.simulation.cloud",
        "https://photonforge.dev-simulation.cloud",
        "https://photonforge.uat-simulation.cloud",
        "https://local-photonforge.dev-simulation.cloud:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "X-Correlation-ID",
    ],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=1728000,  # 20 days, matching nginx config
)


def get_worker(app, project_id: ProjectId):
    worker, work_queue, response_queue = app.state.workers.get(project_id, (None, None, None))
    if worker is None or not worker.is_alive():
        app.state.logger.info(f"Creating worker {project_id}")
        work_queue = SimpleQueue()
        response_queue = SimpleQueue()
        worker = Process(
            target=start_worker,
            args=(
                project_id,
                work_queue,
                response_queue,
                app.state.status_queue,
                app.state.log_queue,
            ),
            name=f"W_{project_id}",
            daemon=True,
        )
        worker.start()
        app.state.workers[project_id] = (worker, work_queue, response_queue)

    if not worker.is_alive():
        raise HTTPException(
            status_code=422,
            detail=f"Unable to start worker for project {project_id}.",
        )

    return worker, work_queue, response_queue


@app.get("/")
async def root():
    return {"title": app.title, "description": app.description, "version": app.version}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    root = Path(__file__).parent.parent
    return FileResponse(root / "static" / "icons" / "photonforge.svg")


@app.get("/api/libraries", status_code=200)
async def get_assets(projectId: ProjectId) -> LibrariesResponse:
    _, work_queue, response_queue = get_worker(app, projectId)

    # Discard any leftover data
    while not response_queue.empty():
        response_queue.get()

    work_queue.put(("components", None))

    lib = None
    libraries = []
    while True:
        timeout = time.monotonic() + 10  # 10s timeout
        while response_queue.empty() and time.monotonic() <= timeout:
            await asyncio.sleep(0.1)
        if response_queue.empty():
            raise HTTPException(status_code=404, detail="Unable to retrieve assets.") from None

        data = response_queue.get()
        if data is None:
            if lib is not None:
                libraries.append(lib)
            break
        elif isinstance(data, str):
            if lib is not None:
                libraries.append(lib)
            lib = Library(name=data, components=[])
        elif lib is not None:
            lib.components.append(data)

    num_components = ", ".join(f"{x.name} ({len(x.components)} components)" for x in libraries)
    app.state.logger.debug(f"Loaded {len(libraries)} libraries from {projectId}: {num_components}")
    return LibrariesResponse(libraries=libraries)


@app.post("/api/application/export", status_code=200)
async def phf_export(request: NetlistExportRequest) -> Response:
    _, work_queue, response_queue = get_worker(app, request.projectId)

    # Discard any leftover data
    while not response_queue.empty():
        response_queue.get()

    app.state.logger.debug(f"Submitting phf export for {request.applicationId}")
    work_queue.put(("export", request))

    timeout = time.monotonic() + 10  # 10s timeout
    while response_queue.empty() and time.monotonic() <= timeout:
        await asyncio.sleep(0.1)

    if response_queue.empty():
        raise HTTPException(status_code=404, detail="No worker response.") from None

    success, result = response_queue.get()
    if not success:
        raise HTTPException(status_code=404, detail=result) from None

    path = Path(result)
    data = path.read_bytes()
    path.unlink(True)

    headers = {"Content-Disposition": 'attachment; filename="exported.phf"'}
    return Response(content=data, media_type="application/octet-stream", headers=headers)


@app.post("/api/jobs", status_code=201)
async def submit_job(request: JobSubmissionRequest) -> JobStatus:
    _, work_queue, _ = get_worker(app, request.projectId)

    job_id = uuid4()
    job_status = JobStatus(
        id=job_id,
        projectId=request.projectId,
        applicationId=request.applicationId,
        simulationMode=request.simulationSettings.simulationMode,
        state="queued",
        createdAt=datetime.now(),
        documentHeads=request.documentHeads,
    )
    async with app.state.jobs_lock:
        app.state.jobs[job_id] = job_status

    app.state.logger.debug(f"Submitting job {job_id}")
    work_queue.put((request, job_status))

    return job_status


@app.get("/api/jobs", status_code=200)
async def get_jobs(applicationId: ApplicationId | None = None) -> list[JobStatus]:
    async with app.state.jobs_lock:
        result = list(app.state.jobs.values())
    if applicationId is not None:
        result = [status for status in result if status.applicationId == applicationId]
    return result


@app.get("/api/jobs/{job_id}", status_code=200)
async def get_results(job_id: str) -> JobStatus:
    try:
        job_id = UUID(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Invalid job ID {job_id}.") from None

    async with app.state.jobs_lock:
        job_status = app.state.jobs.get(job_id)
    if job_status is None:
        raise HTTPException(status_code=404, detail=f"Unkonwn job ID {job_id}.")
    return job_status


@app.post("/api/jobs/{job_id}/abort", status_code=202)
async def abort_job(job_id: str, request: JobAbortRequest):
    try:
        job_id = UUID(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Invalid job ID {job_id}.") from None

    async with app.state.jobs_lock:
        job_status = app.state.jobs.get(job_id)
    if job_status is None:
        raise HTTPException(status_code=404, detail=f"Job ID {job_id} not found.")

    if job_status.state in ["succeeded", "failed", "aborted"]:
        raise HTTPException(status_code=409, detail=f"Job already {job_status.state}.")

    worker, work_queue, _ = app.state.workers.get(job_status.projectId, (None, None, None))
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found.")

    if not worker.is_alive():
        raise HTTPException(status_code=404, detail="Worker failed. Job cannot be aborted.")

    app.state.logger.debug(f"Aborting job {job_id}")
    work_queue.put(("abort", job_id, request.reason))


def run():
    parser = ArgumentParser(
        prog="photonforge-server", description=f"{app.description} Version {app.version}"
    )
    parser.add_argument("--host", default="0.0.0.0", help="server host address")
    parser.add_argument("--port", type=int, default=8001, help="server host port")
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        type=lambda s: s.upper(),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="logging verbosity level",
    )
    args = parser.parse_args()

    log_level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(args.log_level)
    uv_log_level = max(log_level, logging.INFO)

    LOG_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(processName)s:%(threadName)s: %(message)s",
                "use_colors": True,
            },
            "uvicorn": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(processName)s:%(threadName)s: %(message)s",
                "use_colors": True,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(client_addr)s: "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "uvicorn": {
                "formatter": "uvicorn",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "photonforge.server": {"handlers": ["default"], "level": log_level, "propagate": False},
            "photonforge.server.queue": {"handlers": [], "level": log_level, "propagate": False},
            "photonforge.server.worker": {"handlers": [], "level": log_level, "propagate": False},
            "uvicorn": {"handlers": ["uvicorn"], "level": uv_log_level, "propagate": False},
            "uvicorn.error": {"level": uv_log_level},
            "uvicorn.access": {"handlers": ["access"], "level": uv_log_level, "propagate": False},
        },
    }
    logging.config.dictConfig(LOG_CONFIG)
    uvicorn.run(app=app, host=args.host, port=args.port, log_config=LOG_CONFIG)


if __name__ == "__main__":
    run()
