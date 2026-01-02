from libzapi import HelpCenter


def test_list_account_custom_claims_and_get(help_center: HelpCenter):
    sections = list(help_center.account_custom_claims.list_all())
    assert len(sections) > 0, "Expected at least one section from the live API"
