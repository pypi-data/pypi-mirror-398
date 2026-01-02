from libzapi import Ticketing


def test_list_and_get_user_fields(ticketing: Ticketing):
    objs = list(ticketing.user_fields.list_all())
    assert len(objs) > 0
    obj = ticketing.user_fields.get_by_id(objs[0].id)
    assert obj.key == objs[0].key
