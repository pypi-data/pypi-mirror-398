import time

from loguru import logger
from pushikoo_interface import (
    Detail,
    Pusher,
    PusherConfig,
    PusherInstanceConfig,
    Struct,
)  # noqa: F401

from pushikoo_adapter_testpusher.api import MockAPIClient
from pushikoo_adapter_testpusher.config import AdapterConfig, InstanceConfig


class TestPusher(
    Pusher[
        AdapterConfig,  # If you don't have any configuration, you can just use PusherConfig
        InstanceConfig,  # If you don't have any configuration, you can just use PusherInstanceConfig
    ]
):
    # This is your Adapter main implementation.
    # If a fatal error occurs (cannot be recovered properly), do not capture it.
    # Exceptions should be raised directly, with the framework responsible for final error handling and logging.

    def __init__(self) -> None:
        logger.debug(
            f"{self.adapter_name}.{self.identifier} initialized"
        )  # We recommend to use loguru for logging

    def _create_api(self) -> MockAPIClient:
        """Create API client instance with current config (supports hot-reload)."""
        return MockAPIClient(
            token=self.config.authentications[self.instance_config.auth].token,
            userid=self.config.authentications[self.instance_config.auth].userid,
            # You can use self.ctx to access to framework context.
            # Framework provides proxies via ctx
            proxies=self.ctx.get_proxies(),  # {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        )

    def push(self, content: Struct) -> None:
        api = self._create_api()
        api.push(content.asmarkdown(), self.instance_config.to_userid)
