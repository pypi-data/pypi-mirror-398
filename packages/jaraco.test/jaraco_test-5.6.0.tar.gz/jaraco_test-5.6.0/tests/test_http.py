from __future__ import annotations

import urllib.request

import pytest


@pytest.mark.usefixtures("needs_internet")
def test_needs_internet() -> None:
    """
    This test should always succeed or be skipped.
    """
    urllib.request.urlopen('http://pypi.org/')


@pytest.mark.network
def test_network_marker() -> None:
    """
    This test should always succeed or be skipped.
    """
    urllib.request.urlopen('http://pypi.org/')
