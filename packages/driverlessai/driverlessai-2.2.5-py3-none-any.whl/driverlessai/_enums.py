from enum import Enum
from enum import IntEnum


class DownloadType(str, Enum):
    """Used to determine what type of resources to download"""

    FILES = "files"
    DATASETS = "datasets_files"
    LOGS = "log_files"


class JobStatus(IntEnum):
    SYNCING = -4
    SCHEDULED = -3
    FINISHING = -2
    RUNNING = -1
    COMPLETE = 0
    CANCELLED = 1
    FAILED = 2
    ABORTED_BY_USER = 3
    ABORTED_BY_RESTART = 4
    TIMED_OUT = 5

    # Explainer related status
    INCOMPATIBLE = 106

    def __init__(self, status: int) -> None:
        self.message = {
            -4: "Syncing",
            -3: "Scheduled",
            -2: "Finishing",
            -1: "Running",
            0: "Complete",
            1: "Cancelled",
            2: "Failed",
            3: "Aborted",
            4: "Aborted (by restart)",
            5: "Job timed out",
            106: "Incompatible explainer",
        }[status]
