from libzapi.application.commands.help_center.user_segments_cmds import (
    CreateUserSegmentCmd,
    UpdateUserSegmentCmd,
)


def to_payload_create(cmd: CreateUserSegmentCmd) -> dict:
    payload = {
        "user_segment": {
            "name": cmd.name,
            "user_type": cmd.user_type,
            "tags": cmd.tags or [],
            "or_tags": cmd.or_tags or [],
            "added_user_ids": cmd.added_user_ids or [],
            "groups_ids": cmd.groups_ids or [],
            "organization_ids": cmd.organization_ids or [],
        }
    }
    return payload


def to_payload_update(cmd: UpdateUserSegmentCmd) -> dict:
    fields = (
        "name",
        "user_type",
        "tags",
        "or_tags",
        "added_user_ids",
        "groups_ids",
        "organization_ids",
    )

    patch = {field: getattr(cmd, field) for field in fields if getattr(cmd, field) is not None}

    return {"user_segment": patch}
