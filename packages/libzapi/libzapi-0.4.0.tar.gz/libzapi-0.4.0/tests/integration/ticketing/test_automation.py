from libzapi import Ticketing


def test_list_and_get_automation(ticketing: Ticketing):
    itens = list(ticketing.automations.list_all())
    assert len(itens) > 0
    item = ticketing.automations.get(itens[0].id)
    assert item.raw_title == itens[0].raw_title
