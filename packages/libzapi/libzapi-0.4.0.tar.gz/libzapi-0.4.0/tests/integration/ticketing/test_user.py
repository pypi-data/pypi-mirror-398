import itertools

from libzapi import Ticketing


def test_list_and_get_user(ticketing: Ticketing):
    objs = list(itertools.islice(ticketing.users.list_all(), 1000))
    assert len(objs) > 0
    obj = ticketing.users.get_by_id(objs[0].id)
    assert obj.id == objs[0].id
