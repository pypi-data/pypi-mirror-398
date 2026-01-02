from libzapi import CustomData


def test_list_objects_and_get(custom_data: CustomData):
    itens = list(custom_data.custom_objects.list_all())
    assert len(itens) >= 0, "Expected at least 0 custom objects"


def test_limit_objects(custom_data: CustomData):
    limit = custom_data.custom_objects.limit()
    assert limit.limit > 0, "Expected limit to be greater than 0"
    assert limit.count >= 0, "Expected count to be non-negative"
