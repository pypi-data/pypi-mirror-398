from libzapi import Ticketing


def test_list_and_get_support_settings(ticketing: Ticketing):
    addresses = list(ticketing.support_addresses.list())
    assert len(addresses) > 0
    address = ticketing.support_addresses.get(addresses[0].id)
    assert address.name == addresses[0].name
