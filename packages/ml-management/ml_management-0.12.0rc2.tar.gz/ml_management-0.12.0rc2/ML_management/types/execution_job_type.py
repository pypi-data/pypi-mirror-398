from enum import Enum


class ExecutionJobType(str, Enum):
    LOCAL = "local"
    MLM = "mlm"
    CODE = "code"
