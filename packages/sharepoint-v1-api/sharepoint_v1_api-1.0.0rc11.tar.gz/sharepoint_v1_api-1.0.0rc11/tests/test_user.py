import json
from unittest.mock import MagicMock

import pytest
from requests import Response, Session

from sharepoint import SharePointUser


def _mock_response(data: dict, status_code: int = 200) -> Response:
    """Create a minimal ``requests.Response`` object with JSON data."""
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.text = json.dumps(data)
    mock_resp.request = MagicMock()
    mock_resp.request.url = "https://example.com/_api/Web/CurrentUser"
    return mock_resp


@pytest.fixture
def mock_session():
    """Provide a mocked ``requests.Session``."""
    return MagicMock(spec=Session)


def test_user_properties_success(mock_session):
    """Verify that SharePointUser correctly exposes metadata fields."""
    user_data = {
        "d": {
            "Id": 42,
            "Title": "John Doe",
            "Email": "john.doe@example.com"
        }
    }
    mock_session.get.return_value = _mock_response(user_data)

    user = SharePointUser(
        site_user_url="https://example.com/_api/Web/CurrentUser",
        session=mock_session,
    )

    assert user.id == 42
    assert user.title == "John Doe"
    assert user.email == "john.doe@example.com"
    # Username derived from email
    assert user.username == "john.doe"


def test_user_missing_email_returns_none_username(mock_session):
    """When the Email field is missing, ``username`` should be ``None``."""
    user_data = {
        "d": {
            "Id": 7,
            "Title": "Alice"
            # Email omitted
        }
    }
    mock_session.get.return_value = _mock_response(user_data)

    user = SharePointUser(
        site_user_url="https://example.com/_api/Web/CurrentUser",
        session=mock_session,
    )

    assert user.id == 7
    assert user.title == "Alice"
    assert user.email is None
    assert user.username is None


def test_user_no_metadata_returns_none_for_all_fields(mock_session):
    """If the API returns an empty payload, all properties should be ``None``."""
    empty_data = {"d": {}}
    mock_session.get.return_value = _mock_response(empty_data)

    user = SharePointUser(
        site_user_url="https://example.com/_api/Web/CurrentUser",
        session=mock_session,
    )

    assert user.id is None
    assert user.title is None
    assert user.email is None
    assert user.username is None
