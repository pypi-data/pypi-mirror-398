from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Via:
    channel: str
    source: dict
    rel: str
