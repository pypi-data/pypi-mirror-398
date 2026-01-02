import itertools

from libzapi import Ticketing


def test_list_and_get(ticketing: Ticketing):
    objs = list(itertools.islice(ticketing.organizations.list_all(), 1000))
    assert len(objs) > 0
    obj = ticketing.organizations.get_by_id(objs[0].id)
    assert obj.id == objs[0].id


def test_search(ticketing: Ticketing):
    objs = list(itertools.islice(ticketing.organizations.search(name="Sample Company"), 1000))
    assert len(objs) > 0
