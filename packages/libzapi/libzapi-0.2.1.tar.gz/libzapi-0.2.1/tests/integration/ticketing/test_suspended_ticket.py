from libzapi import Ticketing


def test_list_and_get(ticketing: Ticketing):
    collection = list(ticketing.suspended_tickets.list_all())
    if len(collection) > 0:
        item = ticketing.suspended_tickets.get(collection[0].id)
        assert item.name == collection[0].name
    assert isinstance(collection, list)
