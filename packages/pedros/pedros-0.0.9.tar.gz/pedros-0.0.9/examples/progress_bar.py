import time

from pedros.logger import get_logger
from pedros.progress_bar import progbar


def run_demo(backend = "auto"):
    logger = get_logger()
    logger.info(f"Using backend: {backend}")
    for _ in progbar(range(10), backend=backend):
        time.sleep(0.1)


if __name__ == "__main__":
    run_demo("none")
    run_demo("rich")
    run_demo("tqdm")
    run_demo("auto")
    run_demo("dummy")
