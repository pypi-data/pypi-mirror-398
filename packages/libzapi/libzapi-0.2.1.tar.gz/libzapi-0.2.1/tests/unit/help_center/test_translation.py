from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.translation import Translation
from hypothesis import given

strategy = builds(
    Translation,
    title=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Translation) -> None:
    assert model.logical_key.as_str() == "translation:cciia"
