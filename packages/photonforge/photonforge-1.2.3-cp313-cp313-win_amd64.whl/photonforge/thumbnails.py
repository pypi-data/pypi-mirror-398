from collections import defaultdict

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files


def _load(name):
    global thumbnails, _thumb_dir
    thumbnails[name.encode("utf-8")] = _thumb_dir.joinpath(name + ".svg").read_text()


_thumb_dir = files("photonforge").joinpath("thumbnails")

_default = _thumb_dir.joinpath("black_box.svg").read_text()

thumbnails = defaultdict(lambda: _default)

_load("bend")
_load("black_box")
_load("bondpad")
_load("connection")
_load("crossing")
_load("cw_laser")
_load("dc")
_load("dual_mrr")
_load("edge_coupler")
_load("electrical_termination")
_load("eo_ps")
_load("grating_coupler")
_load("laser")
_load("mmi1x2")
_load("mmi2x2")
_load("mrm")
_load("mrr")
_load("mzm")
_load("photodiode")
_load("psgc")
_load("psr")
_load("s-bend")
_load("source")
_load("taper")
_load("termination")
_load("to_ps")
_load("transition")
_load("u-bend")
_load("wdm")
_load("wg")
_load("y-splitter")
