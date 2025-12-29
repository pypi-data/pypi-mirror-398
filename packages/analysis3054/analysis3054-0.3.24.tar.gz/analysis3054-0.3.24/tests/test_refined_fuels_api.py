from unittest.mock import MagicMock, patch

import pandas as pd

from analysis3054.refined_fuels_api import (
    MAX_PAGE_SIZE,
    RefinedFuelsUSMDClient,
    request_access_token,
)


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class DummySession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return self.responses.pop(0)


def test_request_access_token_extracts_data_block():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"access_token": "abc123"}}
    mock_response.raise_for_status.return_value = None
    with patch("requests.post", return_value=mock_response) as post_mock:
        token = request_access_token(client_id="id", client_secret="secret", audience="aud")
    assert token == "abc123"
    post_mock.assert_called_once()


def test_fetch_padd_daily_paginates_and_builds_headers():
    session = DummySession(
        responses=[
            DummyResponse([{"period": "2024-01-01", "region": "1"}]),
            DummyResponse([]),
        ]
    )
    client = RefinedFuelsUSMDClient(api_key="key123", session=session)
    df = client.fetch_padd_daily()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert session.calls[0]["headers"]["apiKey"] == "key123"
    assert session.calls[0]["params"]["pageSize"] == MAX_PAGE_SIZE
    assert session.calls[0]["params"]["page"] == 1


def test_non_list_payload_raises_value_error():
    session = DummySession(responses=[DummyResponse({"unexpected": "structure"})])
    client = RefinedFuelsUSMDClient(api_key="key123", session=session)
    try:
        client.fetch_coverage_daily()
    except ValueError as exc:  # noqa: PERF203
        assert "Unexpected response" in str(exc)
    else:  # pragma: no cover
        assert False, "Expected ValueError for non-list payload"


def test_paginate_rejects_invalid_page_size_and_page():
    client = RefinedFuelsUSMDClient(api_key="key123", session=DummySession([]))

    for kwargs, message in [({"pageSize": 0}, "pageSize"), ({"page": 0}, "page")]:
        try:
            client._paginate("/padd-daily", params=kwargs)
        except ValueError as exc:  # noqa: PERF203
            assert message in str(exc)
        else:  # pragma: no cover
            assert False, "Expected ValueError for invalid pagination arguments"

