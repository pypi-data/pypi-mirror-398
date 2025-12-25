from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentSession:
    csrf_token: str
