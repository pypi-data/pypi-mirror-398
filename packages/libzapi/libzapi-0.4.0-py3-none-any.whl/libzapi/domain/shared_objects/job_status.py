from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class JobResult:
    index: int
    id: str
    account_id: int

@dataclass(frozen=True, slots=True)
class JobStatus:
    id: str
    job_type: str
    url: str
    total: int
    progress: str
    status: str
    message: str
    results: Optional[list[JobResult]] = None