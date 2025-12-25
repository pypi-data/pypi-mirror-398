from libzapi import CustomData


def test_list_objects_and_get(custom_data: CustomData):
    sample = "sample_object"
    itens = list(custom_data.custom_object_fields.list_all(sample))
    assert len(itens) > 0, "Expected at least 1 custom object fields"
