from libzapi.domain.models.ticketing.ticket_field import TicketField


def to_payload(entity: TicketField) -> dict:
    """Convert domain model back to Zendesk's JSON shape."""
    return {
        "ticket_field": {
            "title": entity.title,
            "type": entity.type,
            "required": entity.required,
        }
    }
