from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.redirect_rule import RedirectRule
from hypothesis import given

strategy = builds(
    RedirectRule,
    id=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: RedirectRule):
    assert model.logical_key.as_str() == "redirect_rule:id_cciia"
