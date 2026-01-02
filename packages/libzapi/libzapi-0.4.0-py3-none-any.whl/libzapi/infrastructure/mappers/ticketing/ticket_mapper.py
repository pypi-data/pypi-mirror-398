from libzapi.application.commands.ticketing.ticket_cmds import CreateTicketCmd, UpdateTicketCmd


def to_payload_create(cmd: CreateTicketCmd) -> dict:
    return {
        "ticket": {
            "subject": cmd.subject,
            "custom_fields": [{"id": cf.id,
                               "value": cf.value} for cf in cmd.custom_fields],
            "description": cmd.description,
            "priority": cmd.priority,
            "type": cmd.type,
            "group_id": cmd.group_id,
            "requester_id": cmd.requester_id,
            "organization_id": cmd.organization_id,
            "problem_id": cmd.problem_id,
            "tags": cmd.tags,
            "ticket_form_id": cmd.ticket_form_id,
            "brand_id": cmd.brand_id,
        }
    }


def to_payload_update(cmd: UpdateTicketCmd) -> dict:
    patch = {}
    if cmd.subject:
        patch["subject"] = cmd.subject
    if cmd.custom_fields:
        patch["custom_fields"] = [{"id": cf.id,
                               "value": cf.value} for cf in cmd.custom_fields]
    if cmd.description:
        patch["description"] = cmd.description
    if cmd.priority:
        patch["priority"] = cmd.priority
    if cmd.type:
        patch["type"] = cmd.type
    if cmd.group_id:
        patch["group_id"] = cmd.group_id
    if cmd.requester_id:
        patch["requester_id"] = cmd.requester_id
    if cmd.organization_id:
        patch["organization_id"] = cmd.organization_id
    if cmd.problem_id:
        patch["problem_id"] = cmd.problem_id
    if cmd.tags:
        patch["tags"] = cmd.tags
    if cmd.ticket_form_id:
        patch["ticket_form_id"] = cmd.ticket_form_id
    if cmd.brand_id:
        patch["brand_id"] = cmd.brand_id
    return {"ticket": patch}
