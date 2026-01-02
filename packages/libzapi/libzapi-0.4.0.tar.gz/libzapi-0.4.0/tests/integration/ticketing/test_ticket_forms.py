from libzapi import Ticketing


def test_list_ticket_forms(ticketing: Ticketing):
    ticket_forms = list(ticketing.ticket_forms.list_all())
    assert len(ticket_forms) > 0, "Expected at least one group from the live API"
