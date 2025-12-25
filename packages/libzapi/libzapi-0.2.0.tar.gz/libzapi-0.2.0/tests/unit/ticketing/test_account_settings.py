from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.account_settings import Settings, Branding

account_setting_strategy = builds(
    Settings,
    branding=builds(
        Branding,
        favicon_url=just(""),
    ),
)


@given(account_setting_strategy)
def test_account_setting_attr(setting: Settings) -> None:
    assert setting.branding.favicon_url == ""
