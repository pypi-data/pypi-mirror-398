from pedros.dependency_check import check_dependency
from pedros.logger import get_logger


def progbar(iterable, *args, **kwargs):
    """
    Provides a utility function to display a progress bar for iterables. Based on the
    availability of third-party libraries, such as 'rich' or 'tqdm', it dynamically
    selects the appropriate library to show the progress bar. If neither library is
    installed, it logs a warning and returns the original iterable without any
    progress tracking. If both libraries are installed, it uses 'rich' by default.

    :param iterable: The iterable for which progress needs to be tracked.
    :type iterable: Iterable
    :param args: Additional arguments passed to the progress bar implementation.
    :type args: tuple
    :param kwargs: Additional keyword arguments passed to the progress bar implementation.
    :type kwargs: dict
    :return: A wrapped iterable that provides progress tracking if a compatible library is available; otherwise, returns the original iterable.
    :rtype: Any
    """
    logger = get_logger()

    description = kwargs.get("description")

    if check_dependency("rich"):
        from rich.progress import track

        return track(iterable, *args, **kwargs)

    elif check_dependency("tqdm"):
        from tqdm import tqdm

        if description and "desc" not in kwargs:
            kwargs = kwargs.copy()
            kwargs["desc"] = kwargs.pop("description")

        return tqdm(iterable, *args, **kwargs)

    else:
        logger.warning(
            "No progress bar library found. Install either 'rich' or 'tqdm' to enable progress bars."
        )
        return iterable
