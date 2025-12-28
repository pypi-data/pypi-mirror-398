from dataclasses import dataclass
from typing import Dict, Any, Callable


@dataclass
class HelperConfig:
    # config
    svc: str = 'common'  # aicp / maas / model / docker / epfs

    # log
    logger = None


class HelperConfigBuilder:

    def __init__(self):
        self.config = {}

    def svc(self, svc: str):
        self.config['svc'] = svc
        return self

    def logger(self, logger):
        self.config['logger'] = logger
        return self

    def build(self):
        return HelperConfig(**self.config)

    def create_helper(self):
        return Helper(self.build())


class Helper:
    def __init__(self, config: HelperConfig):
        self.config = config

    def init_and_watch_config(self,
                              header: dict[str, str],
                              callback: Callable[[dict[str, Any]], None] = None,
                              custom_config: Dict[str, Any]|None=None,
                              config_server: str = None) -> dict[str, Any]:
        from aicp_helper.aicp_config import AicpConfig
        aicp_config = AicpConfig(self.config, header, callback, custom_config, config_server)
        return aicp_config.aicp_config
