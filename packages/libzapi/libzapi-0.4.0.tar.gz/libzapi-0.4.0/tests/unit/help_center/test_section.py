from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.section import Section
from hypothesis import given

strategy = builds(
    Section,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Section):
    assert model.logical_key.as_str() == "section:cciia"
