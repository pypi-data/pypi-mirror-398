from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.theme import Theme
from hypothesis import given

strategy = builds(
    Theme,
    name=just("cciiA"),
    version=just("1.0.0"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Theme):
    assert model.logical_key.as_str() == "theme:v_1.0.0_cciia"
