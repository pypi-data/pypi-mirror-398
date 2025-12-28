from dataclasses import dataclass


@dataclass
class StartLogging:
    component_execution_id: str
    instance_execution_id: str


@dataclass
class DeployResult:
    code: int
    message: str
