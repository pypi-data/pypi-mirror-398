import os
from typing import Type, TypeVar

import pytest

from libzapi import Ticketing, HelpCenter, CustomData

T = TypeVar("T")


@pytest.fixture(scope="session")
def ticketing():
    """Creates a real Ticketing client if environment variables are set."""
    return _generic_zendesk_client(Ticketing)


@pytest.fixture(scope="session")
def custom_data():
    """Creates a real Help Center client if environment variables are set."""
    return _generic_zendesk_client(CustomData)


@pytest.fixture(scope="session")
def help_center():
    """Creates a real Help Center client if environment variables are set."""
    return _generic_zendesk_client(HelpCenter)


def _generic_zendesk_client(client_cls: Type[T]) -> T:
    base_url = os.getenv("ZENDESK_URL")
    email = os.getenv("ZENDESK_EMAIL")
    api_token = os.getenv("ZENDESK_TOKEN")

    if not (base_url and email and api_token):
        pytest.skip("Zendesk credentials not provided. Skipping live API tests.")

    return client_cls(
        base_url=base_url,
        email=email,
        api_token=api_token,
    )
