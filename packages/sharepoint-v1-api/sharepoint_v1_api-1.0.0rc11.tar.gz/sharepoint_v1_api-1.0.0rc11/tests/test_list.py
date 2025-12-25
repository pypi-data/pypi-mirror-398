import json
from unittest.mock import MagicMock

import pytest
from requests import Response, Session

from sharepoint import SharePointList, SharePointListItem, SharePointListField


def _mock_response(data: dict, status_code: int = 200) -> Response:
    """Create a minimal ``requests.Response`` object with JSON data."""
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.text = json.dumps(data)
    mock_resp.request = MagicMock()
    mock_resp.request.url = "https://example.com/_api/Web/Lists(guid'list')"
    return mock_resp


@pytest.fixture
def mock_session():
    """Provide a mocked ``requests.Session``."""
    return MagicMock(spec=Session)


def test_list_properties_and_metadata(mock_session):
    """Validate ``title`` and ``id`` properties are read from metadata."""
    list_metadata = {
        "d": {
            "Title": "Tasks",
            "Id": "list-id",
            "Items": {"__deferred": {"uri": "https://example.com/_api/Web/Lists(guid'list')/items"}},
            "Fields": {"__deferred": {"uri": "https://example.com/_api/Web/Lists(guid'list')/fields"}},
        }
    }
    mock_session.get.return_value = _mock_response(list_metadata)

    sp_list = SharePointList(
        list_url="https://example.com/_api/Web/Lists(guid'list')",
        session=mock_session,
    )

    assert sp_list.title == "Tasks"
    assert sp_list.id == "list-id"


def test_get_fields_returns_sharepointlistfield_instances(mock_session):
    """``get_fields`` should return a list of ``SharePointListField`` objects."""
    # First call – list metadata (used by property access)
    # Second call – fields endpoint response
    mock_session.get.side_effect = [
        _mock_response(
            {
                "d": {
                    "Fields": {"__deferred": {"uri": "https://example.com/_api/Web/Lists(guid'list')/fields"}}
                }
            }
        ),
        _mock_response(
            {
                "d": {
                    "results": [
                        {
                            "__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list')/fields(1)"},
                            "Title": "Title",
                        },
                        {
                            "__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list')/fields(2)"},
                            "Title": "Created",
                        },
                    ]
                }
            }
        ),
    ]

    sp_list = SharePointList(
        list_url="https://example.com/_api/Web/Lists(guid'list')",
        session=mock_session,
    )

    fields = sp_list.get_fields()
    assert isinstance(fields, list)
    assert len(fields) == 2
    assert all(isinstance(f, SharePointListField) for f in fields)
    # Verify that the underlying URLs are correctly passed to the field ctor
    assert fields[0].field_url == "https://example.com/_api/Web/Lists(guid'list')/fields(1)"
    assert fields[1].field_url == "https://example.com/_api/Web/Lists(guid'list')/fields(2)"


def test_get_items_returns_sharepointlistitem_instances(mock_session):
    """``get_items`` should return a list of ``SharePointListItem`` objects."""
    mock_session.get.side_effect = [
        # metadata request
        _mock_response(
            {
                "d": {
                    "Items": {"__deferred": {"uri": "https://example.com/_api/Web/Lists(guid'list')/items"}}
                }
            }
        ),
        # items endpoint response
        _mock_response(
            {
                "d": {
                    "results": [
                        {
                            "__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list')/items(1)"},
                            "Id": "1",
                        },
                        {
                            "__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list')/items(2)"},
                            "Id": "2",
                        },
                    ]
                }
            }
        ),
    ]

    sp_list = SharePointList(
        list_url="https://example.com/_api/Web/Lists(guid'list')",
        session=mock_session,
    )

    items = sp_list.get_items()
    assert isinstance(items, list)
    assert len(items) == 2
    assert all(isinstance(i, SharePointListItem) for i in items)
    assert items[0].list_item_url == "https://example.com/_api/Web/Lists(guid'list')/items(1)"
    assert items[1].list_item_url == "https://example.com/_api/Web/Lists(guid'list')/items(2)"


def test_get_item_returns_sharepointlistitem(mock_session):
    """``get_item`` should build the correct URL for a single item."""
    mock_session.get.return_value = _mock_response({"d": {}})  # metadata stub

    sp_list = SharePointList(
        list_url="https://example.com/_api/Web/Lists(guid'list')",
        session=mock_session,
    )

    item = sp_list.get_item(item_id="42")
    expected_url = "https://example.com/_api/Web/Lists(guid'list')/items(42)"
    assert isinstance(item, SharePointListItem)
    assert item.list_item_url == expected_url


def test_create_item_posts_and_returns_sharepointlistitem(mock_session):
    """``create_item`` performs two POST calls and returns a ``SharePointListItem``."""
    # First POST – contextinfo to obtain form digest
    contextinfo_resp = MagicMock()
    contextinfo_resp.json.return_value = {
        "d": {"GetContextWebInformation": {"FormDigestValue": "digest-token"}}
    }

    # Second POST – actual item creation, returns metadata with URI
    create_resp = MagicMock()
    create_resp.json.return_value = {
        "d": {"__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list')/items(99)"}}
    }

    mock_session.post.side_effect = [contextinfo_resp, create_resp]

    # get metadata for items URL (first GET)
    mock_session.get.return_value = _mock_response(
        {
            "d": {
                "Items": {"__deferred": {"uri": "https://example.com/_api/Web/Lists(guid'list')/items"}}
            }
        }
    )

    sp_list = SharePointList(
        list_url="https://example.com/_api/Web/Lists(guid'list')",
        session=mock_session,
    )

    new_item = sp_list.create_item({"Title": "New task"})
    assert isinstance(new_item, SharePointListItem)
    assert new_item.list_item_url == "https://example.com/_api/Web/Lists(guid'list')/items(99)"
    # Verify the two POST calls were made
    assert mock_session.post.call_count == 2