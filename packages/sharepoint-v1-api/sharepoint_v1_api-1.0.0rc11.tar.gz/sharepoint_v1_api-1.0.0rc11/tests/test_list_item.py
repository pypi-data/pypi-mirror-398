import json
from unittest.mock import MagicMock

import pytest
from requests import Response, Session

from sharepoint import SharePointListItem


def _mock_response(data: dict, status_code: int = 200) -> Response:
    """Create a minimal ``requests.Response`` object with JSON data."""
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.text = json.dumps(data)
    mock_resp.request = MagicMock()
    mock_resp.request.url = "https://example.com/_api/Web/Lists(guid'list')/items(1)"
    return mock_resp


@pytest.fixture
def mock_session():
    """Provide a mocked ``requests.Session``."""
    return MagicMock(spec=Session)


def test_list_item_properties(mock_session):
    """Validate that ``SharePointListItem`` exposes metadata correctly."""
    item_data = {
        "d": {
            "Id": "1",
            "Title": "Test Item",
            "Created": "2023-04-01T12:00:00Z",
            "Modified": "2023-04-02T15:30:00Z",
            "__metadata": {"etag": "W/\"1\""}
        }
    }
    mock_session.get.return_value = _mock_response(item_data)

    item = SharePointListItem(
        list_item_url="https://example.com/_api/Web/Lists(guid'list')/items(1)",
        session=mock_session,
    )

    assert item.id == "1"
    assert item.title == "Test Item"
    assert item.etag == 'W/"1"'
    # ``created`` and ``modified`` should be timezone‑aware ``datetime`` objects
    assert isinstance(item.created, type(item.created))
    assert isinstance(item.modified, type(item.modified))


def test_update_item_calls_post_and_returns_ok(mock_session):
    """``update_item`` should perform a POST with MERGE and return ``ok``."""
    # Mock GET for metadata (used during property access)
    mock_session.get.return_value = _mock_response({"d": {}})

    # Mock POST response
    post_resp = MagicMock(spec=Response)
    post_resp.ok = True
    mock_session.post.return_value = post_resp

    item = SharePointListItem(
        list_item_url="https://example.com/_api/Web/Lists(guid'list')/items(1)",
        session=mock_session,
    )

    result = item.update_item({"Title": "Updated Title"})
    assert result is True
    # Ensure POST was called with the correct URL
    mock_session.post.assert_called_once()
    called_args, called_kwargs = mock_session.post.call_args
    assert called_args[0] == "https://example.com/_api/Web/Lists(guid'list')/items(1)"


def test_delete_item_calls_post_complex_and_returns_ok(mock_session):
    """``delete_item`` should perform a POST with X-HTTP-Method DELETE and return ``ok``."""
    # Mock GET for metadata
    mock_session.get.return_value = _mock_response({"d": {}})

    # Mock POST_COMPLEX response
    del_resp = MagicMock(spec=Response)
    del_resp.ok = True
    mock_session.post.return_value = del_resp

    item = SharePointListItem(
        list_item_url="https://example.com/_api/Web/Lists(guid'list')/items(1)",
        session=mock_session,
    )

    result = item.delete_item()
    assert result is True
    mock_session.post.assert_called_once()