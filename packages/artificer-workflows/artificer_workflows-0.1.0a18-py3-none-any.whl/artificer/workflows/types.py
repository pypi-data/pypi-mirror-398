from enum import Enum


class WorkflowStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETE"
    FAILED = "FAILED"


class StepStatus(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
