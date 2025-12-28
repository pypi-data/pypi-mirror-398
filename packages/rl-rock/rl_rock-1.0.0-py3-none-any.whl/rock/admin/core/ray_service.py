import ray

from rock.config import RayConfig
from rock.logger import init_logger

logger = init_logger(__name__)


class RayService:
    def __init__(self, config: RayConfig):
        self._config = config

    def init(self):
        ray.init(
            address=self._config.address,
            runtime_env=self._config.runtime_env,
            namespace=self._config.namespace,
            resources=self._config.resources,
        )
        logger.info("end to init ray")
