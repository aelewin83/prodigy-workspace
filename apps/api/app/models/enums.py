from enum import Enum


class MemberRole(str, Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class TestResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    NA = "N/A"


class TestClass(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class CompSourceType(str, Enum):
    PUBLIC_CONNECTOR = "public_connector"
    PRIVATE_FILE = "private_file"
    MANUAL = "manual"


class ListingSourceType(str, Enum):
    PUBLIC_WEB = "public_web"
    PUBLIC_DATASET = "public_dataset"
    PRIVATE_FILE = "private_file"
    MANUAL = "manual"


class CompRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class UnitType(str, Enum):
    STUDIO = "studio"
    BR1 = "1BR"
    BR2 = "2BR"
    BR3 = "3BR"
    BR4_PLUS = "4BR+"


class VarianceBasis(str, Enum):
    AVG = "avg"
    MEDIAN = "median"


class DealGateState(str, Enum):
    NO_RUN = "NO_RUN"
    KILL = "KILL"
    ADVANCE = "ADVANCE"


class DealStatus(str, Enum):
    KILL = "KILL"
    REVIEW = "REVIEW"
    ADVANCE = "ADVANCE"
