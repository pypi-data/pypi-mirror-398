import os
import threading
import time
import traceback
from typing import Dict, Any, Callable

import httpx
import redis

from aicp_helper.const import LOG_TAG, now
from aicp_helper.helper import HelperConfig

PATH = "/kapis/config.kubesphere.io/v1/configs"


class AicpConfig:

    def __init__(self,
                 helper_config: HelperConfig,
                 header: dict[str, str]|None=None,
                 callback: Callable[[dict[str, Any]], None]=None,
                 custom_config: Dict[str, Any]|None=None,
                 config_server=None):
        self.helper_config = helper_config
        self.header = header
        self.custom_config = custom_config
        self.callback = callback
        self.config_server = config_server or "http://config-server-service.aicp-system:8000"

        self.aicp_config = {}
        self.load_or_fresh_aicp_config()

        if not os.getenv("ENV_CONF"):
            threading.Thread(target=self.watch_config, daemon=True).start()


    def load_or_fresh_aicp_config(self):
        self.aicp_config = self.get_aicp_config()
        if self.custom_config:
            self.aicp_config.update(self.custom_config)
        if self.callback:
            self.callback(self.aicp_config)


    def get_aicp_config(self) -> dict[str, Any]|None:
        params = {"svc": [self.helper_config.svc, "common"]}
        retry_times = 10

        while retry_times > 0:
            try:
                ret = httpx.get(self.config_server + PATH, headers=self.header, params=params, timeout=5)
                if ret.status_code == 200:
                    return {item['key']: item['value'] for item in ret.json()["data"]}
                print(f"{LOG_TAG} get config failed [{retry_times}]: [{ret.status_code}][{ret.text}]", flush=True)
            except Exception as e:
                print(f"{LOG_TAG} get config failed [{retry_times}]: {e}", flush=True)

            retry_times -= 1
            if retry_times == 0:
                raise Exception("get config failed")
            time.sleep(2)


    def watch_config(self):
        version = 0
        while True:
            conn = None
            try:
                print(f"{now()} {LOG_TAG} [{os.getpid()}] Attempting to connect to Redis...", flush=True)
                conn = redis.StrictRedis(
                    host=self.aicp_config['redis_host'],
                    port=self.aicp_config['redis_port'],
                    password=self.aicp_config['redis_password'],
                    socket_keepalive=True,
                    socket_connect_timeout=10,
                    health_check_interval=30,
                    decode_responses=True
                )
                pubsub = conn.pubsub(ignore_subscribe_messages=True)
                pubsub.subscribe("notify_config")
                print(f"{now()} {LOG_TAG} [{os.getpid()}]Redis connect success. Listening for config changes...", flush=True)
                for message in pubsub.listen():
                    if message["type"] == "message":
                        new_version = int(message["data"])
                        if new_version != version:
                            print(f"{now()} {LOG_TAG} [{os.getpid()}] Reload config [{new_version}]", flush=True)
                            self.load_or_fresh_aicp_config()
                            version = new_version
            except redis.exceptions.ConnectionError as e:
                print(f"{now()} {LOG_TAG} [{os.getpid()}] Redis connection lost: {e}. retry connect.", flush=True)
            except Exception as e:
                print(f"{now()} {LOG_TAG} [{os.getpid()}] An unexpected error occurred: {e}. Will retry in 10 seconds.", flush=True)
                traceback.print_exc()
                time.sleep(10)
            finally:
                if conn:
                    conn.close()
