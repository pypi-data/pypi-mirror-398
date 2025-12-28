from typing import Any

from pydantic import BaseModel, Field

from rock.deployments.constants import Status


class PhaseStatus(BaseModel):
    status: Status = Status.WAITING
    message: str = "waiting"

    def to_dict(self) -> dict[str, str]:
        return {"status": self.status.value, "message": self.message}


class ServiceStatus(BaseModel):
    phases: dict[str, PhaseStatus] = Field(default_factory=dict)
    port_mapping: dict[int, int] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.phases:
            self.add_phase("image_pull", PhaseStatus())
            self.add_phase("docker_run", PhaseStatus())

    def add_phase(self, phase_name: str, status: PhaseStatus):
        self.phases[phase_name] = status

    def get_phase(self, phase_name: str) -> PhaseStatus:
        return self.phases[phase_name]

    def update_status(self, phase_name: str, status: Status, message: str):
        self.phases[phase_name].status = status
        self.phases[phase_name].message = message

    def add_port_mapping(self, local_port: int, container_port: int):
        self.port_mapping[local_port] = container_port

    def get_port_mapping(self) -> dict[int, int]:
        return self.port_mapping

    def get_mapped_port(self, local_port: int) -> int:
        return self.port_mapping[local_port]

    def __str__(self) -> str:
        """String representation"""
        status_lines = []
        for name, phase in self.phases.items():
            status_lines.append(f"{name}: {phase.status.value} - {phase.message}")
        return "\n".join(status_lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phases": {name: phase.to_dict() for name, phase in self.phases.items()},
            "port_mapping": self.port_mapping,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceStatus":
        """Create ServiceStatus object from dictionary"""
        phases = {}
        for key, phase_data in data.get("phases", {}).items():
            phases[key] = PhaseStatus(status=Status(phase_data["status"]), message=phase_data["message"])

        port_mapping = {}
        for port_value, mapping in data.get("port_mapping", {}).items():
            port_mapping[int(port_value)] = mapping

        return cls(phases=phases, port_mapping=port_mapping)
