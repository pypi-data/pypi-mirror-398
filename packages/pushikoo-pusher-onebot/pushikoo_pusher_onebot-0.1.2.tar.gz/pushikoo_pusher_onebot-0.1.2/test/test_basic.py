import os
from pathlib import Path

from dotenv import load_dotenv
from pushikoo_interface import (
    Pusher,
    Struct,
    get_adapter_test_env,
    run_pusher_basic_flow,
)

from pushikoo_pusher_onebot.config import AdapterConfig, Bot, Contact, InstanceConfig


def test_basic_flow():
    load_dotenv()
    adapter_config = AdapterConfig(
        bots={
            "bot0": Bot(
                token=os.getenv("BOT_TOKEN"),
                url=os.getenv("BOT_URL"),
            )
        }
    )
    instance_config = InstanceConfig(
        bot="bot0",
        contact=Contact(
            id=os.getenv("TARGET_ID"), private=os.getenv("TARGET_PRIVATE") == "true"
        ),
    )
    pusher, ctx = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_config=adapter_config,
        adapter_instance_config=instance_config,
    )
    run_pusher_basic_flow(pusher, ctx)


if __name__ == "__main__":
    test_basic_flow()
