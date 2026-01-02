from libzapi.application.commands.help_center.account_custom_claim_cmds import (
    CreateCustomClaimCmd,
    UpdateCustomClaimCmd,
)


def to_payload_create(cmd: CreateCustomClaimCmd) -> dict:
    payload = {
        "custom_claim": {
            "claim_identifier": cmd.claim_identifier,
            "claim_value": cmd.claims_value,
            "claim_description": cmd.claim_description,
        }
    }
    return payload


def to_payload_update(cmd: UpdateCustomClaimCmd) -> dict:
    """Can only update position according to Zendesk API docs."""
    fields = (
        "claim_identifier",
        "claim_value",
        "claim_description",
    )

    patch = {field: getattr(cmd, field) for field in fields if getattr(cmd, field) is not None}

    return {"custom_claim": patch}
