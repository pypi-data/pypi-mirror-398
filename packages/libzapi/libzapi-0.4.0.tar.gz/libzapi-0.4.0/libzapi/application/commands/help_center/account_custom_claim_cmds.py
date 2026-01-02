from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateCustomClaimCmd:
    claim_identifier: str
    claim_value: str
    claim_description: str


@dataclass(frozen=True, slots=True)
class UpdateCustomClaimCmd:
    claim_identifier: str
    claim_value: str
    claim_description: str
