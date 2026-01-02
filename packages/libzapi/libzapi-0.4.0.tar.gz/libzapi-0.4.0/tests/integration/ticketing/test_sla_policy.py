from libzapi import Ticketing


def test_list_and_get_sla_policy(ticketing: Ticketing):
    items = list(ticketing.sla_policies.list())
    assert len(items) > 0
    item = ticketing.sla_policies.get(items[0].id)
    assert item.title == items[0].title
