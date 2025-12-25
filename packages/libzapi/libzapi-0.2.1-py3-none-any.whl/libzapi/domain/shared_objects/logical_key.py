from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogicalKey:
    z_type: str
    name: str

    def as_str(self) -> str:
        return f"{self.z_type}:{self.name}"
