from ._dependency import *
from ._runtime_env_config import RuntimeEnvConfig
from ._const import *
from ._utils import *


class RayCluster:

    def __init__(
        self,
        head_ip: str,
        namespace: str = DEFAULT_NAME_SPACE,
        client_port: int = DEFAULT_CLIENT_PORT,
        runtime_env: RuntimeEnvConfig = RuntimeEnvConfig(),
        log_to_driver: bool = True,
    ) -> None:
        assert (
            client_port > MIN_CLIENT_PORT
        ), f"ERROR, client_port must be at lest {MIN_CLIENT_PORT}"
        assert not ray.is_initialized()
        self._head_ip = head_ip
        self._client_port = client_port
        self._namespace = namespace

        # if head_ip is none, excute ray up
        ray.init(
            address=f"ray://{self.head_ip}:{self.client_port}",
            namespace=namespace,
            runtime_env=runtime_env.to_dict(),
            log_to_driver=log_to_driver,
        )
        logger.info(
            f"Ray Cluster Session has been initialized for [{head_ip}:{client_port}]"
        )

    def __enter__(self):
        return self

    def __exit__(self, type, value, trackback):
        logger.debug(f"type: {type} | value: {value} | trackback: {trackback}")
        return self.close()

    def close(self):
        ray.shutdown()

    @property
    def head_ip(self) -> str:
        assert self._head_ip is not None
        return self._head_ip

    @property
    def client_port(self) -> int:
        return self._client_port
