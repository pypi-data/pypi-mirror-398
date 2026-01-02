from libzapi import Ticketing


def test_list_ticket_forms(ticketing: Ticketing):
    itens = list(ticketing.ticket_fields.list_all())
    assert len(itens) > 0, "Expected at least one group from the live API"
