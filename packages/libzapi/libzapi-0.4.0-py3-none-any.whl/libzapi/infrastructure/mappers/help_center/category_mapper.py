from libzapi.application.commands.help_center.category_cmds import (
    CreateCategoryCmd,
    UpdateCategoryCmd,
)


def to_payload_create(cmd: CreateCategoryCmd) -> dict:
    payload = {
        "category": {
            "name": cmd.name,
            "description": cmd.description,
            "locale": cmd.locale,
            "position": cmd.position,
        }
    }
    return payload


def to_payload_update(cmd: UpdateCategoryCmd) -> dict:
    """Can only update position according to Zendesk API docs."""
    patch = {}
    if cmd.position is not None:
        patch["position"] = cmd.position
    return {"category": patch}
