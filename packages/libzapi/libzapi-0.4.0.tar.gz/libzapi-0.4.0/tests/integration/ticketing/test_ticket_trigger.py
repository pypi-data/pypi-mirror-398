from libzapi import Ticketing


def test_list_and_get_ticket_triggers(ticketing: Ticketing):
    triggers = list(ticketing.ticket_triggers.list())
    assert len(triggers) > 0
    address = ticketing.ticket_triggers.get(triggers[0].id)
    assert address.title == triggers[0].title
