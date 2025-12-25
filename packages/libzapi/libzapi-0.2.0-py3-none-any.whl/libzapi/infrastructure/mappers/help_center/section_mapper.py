from libzapi.application.commands.help_center.section_cmds import (
    CreateSectionCmd,
    UpdateSectionCmd,
)


def to_payload_create(cmd: CreateSectionCmd) -> dict:
    payload = {
        "section": {
            "name": cmd.name,
            "description": cmd.description,
            "locale": cmd.locale,
            "position": cmd.position,
            "parent_section_id": cmd.parent_section_id,
        }
    }
    return payload


def to_payload_update(cmd: UpdateSectionCmd) -> dict:
    fields = (
        "name",
        "description",
        "position",
        "category_id",
        "parent_section_id",
    )

    patch = {field: getattr(cmd, field) for field in fields if getattr(cmd, field) is not None}

    # For a case when we want to remove the parent_section_id (i.e., convert a subsection back to a top-level section)
    if cmd.promote_to_top_level:
        patch["parent_section_id"] = None

    return {"section": patch}
