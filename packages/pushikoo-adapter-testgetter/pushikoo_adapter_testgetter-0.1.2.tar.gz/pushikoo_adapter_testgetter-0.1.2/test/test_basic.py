from pathlib import Path

from pushikoo_interface import (
    get_adapter_test_env,
    run_getter_basic_flow,
)


def test_basic_flow():
    getter, ctx = get_adapter_test_env(Path(__file__).parents[1] / "pyproject.toml")
    ids, detail, details = run_getter_basic_flow(getter, ctx)

    # TODO: Edit this, or add more test cases
    pass
