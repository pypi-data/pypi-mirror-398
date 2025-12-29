from __future__ import annotations

from typing import Any, Iterable, Literal, TypeVar, cast

from pedros.dependency_check import check_dependency
from pedros.logger import get_logger

T = TypeVar("T")
Backend = Literal["auto", "rich", "tqdm", "none"]


def progbar(
    iterable: Iterable[T],
    *args: Any,
        backend: Backend | str = "auto",
    **kwargs: Any,
) -> Iterable[T]:
    """
    Displays a progress bar for the provided iterable, using a chosen backend library.

    This function iterates over the elements of the given iterable and optionally displays
    a progress bar using either the `rich` or `tqdm` libraries. The choice of backend can
    be explicitly specified, or automatically determined based on the libraries available
    in the environment. If no supported library is found or the backend is set to "none",
    no progress bar will be displayed and the original iterable will be returned.

    :param iterable:
        The iterable whose elements should be iterated over with an optional progress bar.
    :param args:
        Positional arguments to pass to the progress bar library.
    :param backend:
        The progress bar backend to use. Supported values are:
        - "auto" (default): Automatically selects a backend based on available libraries.
        - "rich": Uses the `rich.progress` library, if available.
        - "tqdm": Uses the `tqdm` library, if available.
        - "none": Disables the progress bar and returns the original iterable.
    :param kwargs:
        Additional keyword arguments to customize the behavior of the progress bar. These
        are dependent on the backend used:
        - For `tqdm`, `desc` and other `tqdm`-specific parameters can be provided.
        - For `rich.progress`, `description` and other `rich`-specific arguments can be used.
    :return:
        The input iterable, optionally wrapped with a progress bar based on the selected backend.
    """
    logger = get_logger()

    allowed = ("auto", "rich", "tqdm", "none")

    if isinstance(backend, str):
        backend_norm = backend.strip().lower()
    else:
        backend_norm = cast(str, backend)

    if backend_norm not in allowed:
        logger.warning(f"Invalid backend '{backend}'. Falling back to 'auto'.")
        backend_norm = "auto"

    backend_lit = cast(Backend, backend_norm)

    def _select_backend() -> Backend:
        if backend_lit == "none":
            return "none"

        rich_ok = check_dependency("rich")
        tqdm_ok = check_dependency("tqdm")

        if backend_lit == "rich":
            if rich_ok:
                return "rich"
            logger.warning("backend='rich' requested but 'rich' is not installed. Falling back.")
            return "tqdm" if tqdm_ok else "none"

        if backend_lit == "tqdm":
            if tqdm_ok:
                return "tqdm"
            logger.warning("backend='tqdm' requested but 'tqdm' is not installed. Falling back.")
            return "rich" if rich_ok else "none"

        if backend_lit == "auto":
            if rich_ok:
                return "rich"
            if tqdm_ok:
                return "tqdm"

        logger.warning("No progress bar library found. Install either 'rich' or 'tqdm'.")
        return "none"

    def _normalize_kwargs(for_backend: Backend) -> dict[str, Any]:
        local = dict(kwargs)

        has_description = "description" in local
        has_desc = "desc" in local

        if for_backend == "tqdm" and has_description and not has_desc:
            local["desc"] = local.pop("description")

        if for_backend == "rich" and has_desc and not has_description:
            local["description"] = local.pop("desc")

        return local

    chosen = _select_backend()

    if chosen == "none":
        return iterable

    if chosen == "rich":
        from rich.progress import track

        local_kwargs = _normalize_kwargs("rich")
        return track(iterable, *args, **local_kwargs)

    if chosen == "tqdm":
        from tqdm import tqdm

        local_kwargs = _normalize_kwargs("tqdm")
        return tqdm(iterable, *args, **local_kwargs)

    logger.warning("Something went wrong. Returning the original iterable.")
    return iterable
