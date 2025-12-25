from os import getenv
from pathlib import Path

from pushikoo_interface import (
    get_adapter_test_env,
    run_getter_basic_flow,
)
from dotenv import load_dotenv

from pushikoo_getter_gh.config import AdapterConfig, InstanceConfig


def test_basic_flow():
    load_dotenv()

    config = AdapterConfig(
        auth={"default": getenv("GITHUB_TOKEN")},
    )
    instance_config = InstanceConfig(repo="Kengxxiao/ArknightsGameData", auth="default")
    getter, ctx = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_config=config,
        adapter_instance_config=instance_config,
    )
    ids, detail, details = run_getter_basic_flow(getter, ctx)

    # Basic assertions
    assert isinstance(ids, list)
    if ids:
        assert detail is not None
        assert details is not None
    print(ids, detail)


if __name__ == "__main__":
    test_basic_flow()
