import asyncio as _a
import pathlib as _p
import queue as _q
import threading as _t
import time as _tm
import typing as _typ

import fastapi as _f
import uvicorn as _uc
from fastapi.middleware.cors import CORSMiddleware as _cors
from fastapi.responses import FileResponse as _fr
from fastapi.responses import StreamingResponse as _sr
from fastapi.staticfiles import StaticFiles as _sf
from fastapi.templating import Jinja2Templates as _j2

import photonforge as _pf


class LiveViewer:
    """Live viewer for PhotonForge objects.

    Args:
        port: Port number used by the viewer server.
        start: If ``True``, the viewer server is automatically started.

    Example:
        >>> from photonforge.live_viewer import LiveViewer
        >>> viewer = LiveViewer()

        >>> component = pf.parametric.straight(port_spec="Strip", length=3)
        >>> viewer(component)

        >>> terminal = pf.Terminal("METAL", pf.Circle(2))
        >>> viewer(terminal)
    """

    def __init__(self, port: int = 0, start: bool = True):
        self.app = _f.FastAPI(
            title="LiveViewer server",
            description="PhotonForge LiveViewer server",
            version=_pf.__version__,
        )

        self.app.add_middleware(
            _cors,
            allow_origins=[],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        root = _p.Path(__file__).parent
        self.app.mount("/static", _sf(directory=root / "static"), name="static")
        self.templates = _j2(directory=root / "templates")

        self.port = port
        self.current_data = ""
        self.server = None

        @self.app.get("/")
        async def home(request: _f.Request):
            return self.templates.TemplateResponse(name="index.html", request=request)

        @self.app.get("/events", include_in_schema=False)
        async def events():
            return _sr(self.generate(), media_type="text/event-stream")

        @self.app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return _fr(root / "static" / "icons" / "photonforge.svg")

        if start:
            self.start()

    async def generate(self):
        while self.server is not None:
            try:
                while not self.queue.empty():
                    self.current_data = self.queue.get_nowait()
            except _q.Empty:
                pass
            if self.current_data == "shutdown":
                return
            if self.current_data:
                yield f"data: {self.current_data}\n\n"
            else:
                yield "data: Waiting for data…\n\n"
            await _a.sleep(0.25)

    def start(self) -> "LiveViewer":
        """Start the server."""
        config = _uc.Config(app=self.app, host="0.0.0.0", port=self.port, log_level="error")
        self.server = _uc.Server(config=config)

        self.server_thread = _t.Thread(target=self.server.run, daemon=False)
        self.server_thread.start()

        self.queue = _q.SimpleQueue()

        while not self.server.started:
            _tm.sleep(0.1)

        for s in self.server.servers:
            for socket in s.sockets:
                self.port = socket.getsockname()[1]
                break
        print(f"LiveViewer started at http://localhost:{self.port}")

        return self

    def stop(self):
        """Stop the server."""
        if self.server is not None:
            self.queue.put("shutdown")
            self.server.should_exit = True
            self.server_thread.join()
            self.server = None
            print("LiveViewer stopped.")

    def __call__(self, item: _typ.Any) -> _typ.Any:
        """Display an item with an SVG representation.

        Args:
            item: Item to be displayed.

        Returns:
            'item'.
        """

        if self.server is not None and hasattr(item, "_repr_svg_"):
            self.queue.put(item._repr_svg_())
        return item

    def display(self, item: _typ.Any) -> _typ.Any:
        """Display an item with an SVG representation.

        Args:
            item: Item to be displayed.

        Returns:
            'item'.
        """
        return self(item)

    def _repr_html_(self) -> str:
        """Returns a clickable link for Jupyter."""
        if self.server is None:
            return "LiveViewer not started."
        return (
            f'Live viewer at <a href="http://localhost:{self.port}" target="_blank">'
            f"http://localhost:{self.port}</a>"
        )

    def __str__(self) -> str:
        if self.server is None:
            return "LiveViewer not started."
        return f"Live viewer at http://localhost:{self.port}"
