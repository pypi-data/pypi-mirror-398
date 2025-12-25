from pathlib import Path

from pushikoo_interface import get_adapter_test_env, run_pusher_basic_flow


def test_basic_flow():
    pusher, ctx = get_adapter_test_env(Path(__file__).parents[1] / "pyproject.toml")
    run_pusher_basic_flow(pusher, ctx)

    # TODO: Edit this, or add more test cases
    pass
