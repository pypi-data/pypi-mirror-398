import collections as _col
import functools as _func
import pathlib as _pth
import threading as _thr
import typing as _typ
import warnings as _warn

from .extension import _content_repr

path: str = "~/.tidy3d/pf_cache"


def _cache_path(name: str) -> _pth.Path:
    return _pth.Path(path).expanduser().resolve() / name[:3]


class _Cache:
    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._data = _col.OrderedDict()
        self._lock = _thr.Lock()

    def __getitem__(self, key: _typ.Any) -> _typ.Any:
        with self._lock:
            value = self._data.get(key, None)
            if value is not None:
                self._data.move_to_end(key)
            return value

    def __setitem__(self, key: _typ.Any, value: _typ.Any) -> None:
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            if self._capacity > 0:
                while len(self._data) >= self._capacity:
                    self._data.popitem(False)

    def clear(self) -> None:
        with self._lock:
            self._data = _col.OrderedDict()

    def set_capacity(self, c) -> None:
        with self._lock:
            self._capacity = c


_s_matrix_cache = _Cache(64)
_tidy3d_model_cache = _Cache(64)
_mode_solver_cache = _Cache(64)
_mode_overlap_cache = _Cache(64)
_pole_residue_fit_cache = _Cache(64)
_all_caches = [
    _s_matrix_cache,
    _tidy3d_model_cache,
    _mode_solver_cache,
    _mode_overlap_cache,
    _pole_residue_fit_cache,
]


def cache_s_matrix(start: _typ.Callable):
    """Decorator that can be used in :func:`Model.start` to cache results."""

    @_func.wraps(start)
    def _start(model, component, frequencies, *args, **kwargs):
        try:
            key = _content_repr(model, component, frequencies, args, kwargs)
        except Exception:
            _warn.warn(
                f"Unable to cache S matrix results for component '{component.name}'.",
                RuntimeWarning,
                2,
            )
            return start(model, component, frequencies, *args, **kwargs)

        result = _s_matrix_cache[key]
        if result is None or (
            hasattr(result, "status") and result.status.get("message") not in ("running", "success")
        ):
            result = start(model, component, frequencies, *args, **kwargs)
            _s_matrix_cache[key] = result
        elif kwargs.get("verbose", False):
            print(f"Using cached result for {component}/{model}.")
        return result

    return _start


def clear_cache() -> None:
    """Clear the runtime caches, but not the file cache.

    The file cache is stored in :data:`photonforge.cache.path`. It can be
    cleared by simply deleting the contents in that directory.
    """
    for c in _all_caches:
        c.clear()


def cache_capacity(capacity: int) -> None:
    """Set the runtime cache capacity.

    Args:
        capacity: Set a new cache capacity. A negative value removes the
          capacity limit.
    """
    for c in _all_caches:
        c.set_capacity(capacity)


def _stat(p: _pth.Path) -> tuple[float, int, _pth.Path]:
    st = p.stat()
    return (max(st.st_ctime, st.st_mtime, st.st_atime), st.st_size, p)


def delete_cached_results(
    *,
    max_file_size: int | None = None,
    total_size_remaining: int | None = None,
    start_from_oldest: bool = True,
    dry_run: bool = True,
) -> tuple[list[_pth.Path], int]:
    """Delete cached simulation results from PhotonForge.

    The cache path is defined by :attr:`cache.path`. Any files in this
    path will be considered for deletion.

    Args:
        max_file_size: If set, delete any files larger than this size (in
          bytes).
        total_size_remaining: If set, leave cached files occupying up to
          this total (in bytes).
        remove_from_oldest: If ``True``, start removing the files from the
          oldest to the newest. Otherwise, use the reverse order.
        dry_run: If ``True``, no files are deleted. Used for test runs.

    Returns:
        List of deleted file paths and total cache size before deletion.

    Examples:
        Remove cached results larger than approximatelly 500 MB

        >>> pf.cache.delete_cached_results(max_file_size=500e6)  # doctest: +SKIP

        Remove cached results starting from the oldest until the total cache
        size is approximatelly 10 GB.

        >>> pf.cache.delete_cached_results(total_size_remaining=10e9)  # doctest: +SKIP

    Warning:
        This operation is irreversible! Deleted files cannot be recovered!
    """
    cache_path = _pth.Path(path).expanduser().resolve()
    sorted_files = sorted(
        (_stat(p) for p in cache_path.glob("**/*") if p.is_file()), reverse=start_from_oldest
    )

    to_remove = []
    total_size = 0
    for _, size, p in sorted_files:
        if max_file_size and size > max_file_size:
            to_remove.append(p)
        else:
            total_size += size
            if total_size_remaining and total_size > total_size_remaining:
                to_remove.append(p)

    if dry_run:
        print(
            "No files have been deleted! Check the returned list to see which files would have "
            "been deleted by this function. To delete the files, re-run with 'dry_run=False'."
        )
    else:
        for p in to_remove:
            p.unlink()

        dirs = [p for p in cache_path.glob("**/*") if p.is_dir()]
        for dir in sorted(dirs, key=str, reverse=True):
            if next(dir.iterdir(), None) is None:
                dir.rmdir()

    return to_remove, total_size
