import time
from unittest.mock import patch
from pedros.dependency_check import check_dependency
from pedros.progress_bar import progbar


def run_demo(label: str):
    print(f"\n--- DEMO: {label} ---")
    check_dependency.cache_clear()

    items = range(5)
    p_bar = progbar(items, description="Processing...")

    impl_type = type(p_bar).__name__
    print(f"Iterator type: {impl_type}")

    for i in p_bar:
        time.sleep(0.1)
        if impl_type == "range":
            print(f"Processing item {i}...")


if __name__ == "__main__":
    run_demo("Native Environment")

    with patch(
        "pedros.dependency_check.find_spec",
        side_effect=lambda n: None if n == "rich" else True,
    ):
        run_demo("Without Rich (Using TQDM)")

    with patch(
        "pedros.dependency_check.find_spec",
        side_effect=lambda n: None if n == "tqdm" else True,
    ):
        run_demo("Without TQDM (Using Rich)")

    with patch("pedros.dependency_check.find_spec", return_value=None):
        run_demo("Without Rich and TQDM (Fallback mode)")
