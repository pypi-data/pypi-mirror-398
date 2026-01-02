from libzapi import Ticketing


def test_list_brand_agent(ticketing: Ticketing):
    results = list(ticketing.brand_agents.list_all())
    assert len(results) > 0
