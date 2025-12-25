from libzapi import Ticketing


def test_list_and_get(ticketing: Ticketing):
    items = list(ticketing.tickets.list())
    assert len(items) > 0
    item = ticketing.tickets.get(items[0].id)
    assert item.id == items[0].id
