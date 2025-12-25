from libzapi import CustomData


def test_list_objects_and_get(custom_data: CustomData):
    sample = "sample_object"
    itens = list(custom_data.custom_object_records.list_all(sample))
    assert len(itens) > 0, "Expected at least 1 custom object fields"


def test_list_objects_and_get_with_sort_and_pagination(custom_data: CustomData):
    sample = "sample_object"
    itens = list(
        custom_data.custom_object_records.list_all(
            custom_object_key=sample, sort_type="id", sort_order="asc", page_size=2
        )
    )
    assert len(itens) > 0, "Expected at least 1 custom object fields"


def test_list_records_limit(custom_data: CustomData):
    limit = custom_data.custom_object_records.limit()
    assert limit.limit > 0, "Expected record limit to be greater than 0"
