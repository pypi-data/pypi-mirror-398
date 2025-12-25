from libzapi.application.commands.ticketing.group_cmds import CreateGroupCmd, UpdateGroupCmd


def to_payload_create(cmd: CreateGroupCmd) -> dict:
    return {
        "group": {
            "name": cmd.name,
            "description": cmd.description,
            "is_public": cmd.is_public,
            "default": cmd.default,
        }
    }


def to_payload_update(cmd: UpdateGroupCmd) -> dict:
    patch = {}
    if cmd.name is not None:
        patch["name"] = cmd.name
    if cmd.description is not None:
        patch["description"] = cmd.description
    if cmd.is_public is not None:
        patch["is_public"] = cmd.is_public
    if cmd.default is not None:
        patch["default"] = cmd.default
    return {"group": patch}
