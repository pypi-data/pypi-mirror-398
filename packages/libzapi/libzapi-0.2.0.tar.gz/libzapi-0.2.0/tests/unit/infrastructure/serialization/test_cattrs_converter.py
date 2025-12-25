from libzapi.domain.models.ticketing.ticket import Source
from libzapi.infrastructure.serialization.cattrs_converter import get_converter


def test_source_converter():
    payload = {"to": {"id": 1}, "from": {"id": 2}, "rel": "x"}
    src = get_converter().structure(payload, Source)
    assert src.from_ == {"id": 2}

    out = get_converter().unstructure(src)
    assert "from" in out and "from_" not in out
