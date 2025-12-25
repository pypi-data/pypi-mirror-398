from libzapi import Ticketing


def test_get_account_settings(ticketing: Ticketing):
    settings = ticketing.account_settings.get()
    assert settings.cdn.cdn_provider == "default"
