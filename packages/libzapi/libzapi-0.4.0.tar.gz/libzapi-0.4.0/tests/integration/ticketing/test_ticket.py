from libzapi import Ticketing


def test_list_and_get(ticketing: Ticketing):
    items = list(ticketing.tickets.list())
    assert len(items) > 0
    item = ticketing.tickets.get(items[0].id)
    assert item.id == items[0].id

def test_create_and_update_ticket(ticketing: Ticketing):
    ticket = ticketing.tickets.create(subject="Test ticket", description="Test ticket description", custom_fields=[
        {"id": 35650075609748, "value": "Test value"},
        {"id": 35650075985428, "value": "Test value 2"}
    ])
    assert ticket.subject == "Test ticket"
    updated_ticket = ticketing.tickets.update(ticket_id=ticket.id, subject="Updated ticket")
    assert updated_ticket.subject == "Updated ticket"

def test_create_many(ticketing: Ticketing):
    many = ticketing.tickets.create_many(
        [
            {"subject": "Test ticket 1", "description": "Test ticket description 1"},
            {"subject": "Test ticket 2", "description": "Test ticket description 2"},
        ]
    )
    assert many.total == 2