from typing_extensions import Self

from rock.deployments.config import DockerDeploymentConfig
from rock.deployments.docker import DockerDeployment
from rock.logger import init_logger
from rock.sandbox.sandbox_actor import SandboxActor

logger = init_logger(__name__)


class RayDeployment(DockerDeployment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_config(cls, config: DockerDeploymentConfig) -> Self:
        return cls(**config.model_dump())

    async def creator_actor(self, actor_name: str):
        return await self._create_sandbox_actor(actor_name)

    async def _create_sandbox_actor(self, actor_name: str):
        """Create sandbox actor instance"""
        if self.config.actor_resource and self.config.actor_resource_num:
            sandbox_actor = SandboxActor.options(
                name=actor_name,
                resources={self.config.actor_resource: self.config.actor_resource_num},
                lifetime="detached",
            ).remote(self._config, self)
        else:
            sandbox_actor = SandboxActor.options(
                name=actor_name,
                lifetime="detached",
            ).remote(self._config, self)
        return sandbox_actor
