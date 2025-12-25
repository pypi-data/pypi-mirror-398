import json
from unittest.mock import MagicMock

import pytest
from requests import Response, Session

from sharepoint import SharePointGroup, SharePointUser


def _mock_response(data: dict, status_code: int = 200) -> Response:
    """Create a minimal ``requests.Response`` object with JSON data."""
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.text = json.dumps(data)
    mock_resp.request = MagicMock()
    mock_resp.request.url = "https://example.com/_api/Web/SiteGroups"
    return mock_resp


@pytest.fixture
def mock_session():
    """Provide a mocked ``requests.Session``."""
    return MagicMock(spec=Session)


def test_group_properties_success(mock_session):
    """Verify that ``SharePointGroup`` correctly exposes title and guid."""
    group_data = {
        "d": {
            "Title": "Project Managers",
            "Id": "group-1234"
        }
    }
    mock_session.get.return_value = _mock_response(group_data)

    group = SharePointGroup(
        group_url="https://example.com/_api/Web/SiteGroups(guid'group-1234')",
        session=mock_session,
    )

    assert group.title == "Project Managers"
    assert group.guid == "group-1234"


def test_group_missing_title_returns_none(mock_session):
    """When the Title field is missing, ``title`` should be ``None``."""
    group_data = {
        "d": {
            "Id": "group-5678"
            # Title omitted
        }
    }
    mock_session.get.return_value = _mock_response(group_data)

    group = SharePointGroup(
        group_url="https://example.com/_api/Web/SiteGroups(guid'group-5678')",
        session=mock_session,
    )

    assert group.title is None
    assert group.guid == "group-5678"


def test_group_user_access(mock_session):
    """A group can be used to retrieve its users via ``SharePointUser``."""
    # The group itself does not expose users directly; this test ensures that
    # the underlying session can be reused to instantiate a user.
    mock_session.get.return_value = _mock_response({"d": {}})  # metadata stub

    group = SharePointGroup(
        group_url="https://example.com/_api/Web/SiteGroups(guid'group-9999')",
        session=mock_session,
    )

    # Manually create a user using the same session to simulate typical usage
    user = SharePointUser(
        site_user_url="https://example.com/_api/Web/CurrentUser",
        session=mock_session,
    )

    # No actual network call; just verify that the user object works with the session
    assert isinstance(user, SharePointUser)
    # The user properties will be ``None`` because we haven't set metadata
    assert user.id is None
    assert user.title is None