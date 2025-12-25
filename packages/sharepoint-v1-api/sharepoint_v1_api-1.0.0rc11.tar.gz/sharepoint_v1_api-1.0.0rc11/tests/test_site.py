import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from requests import Response, Session

from sharepoint import SharePointSite, SharePointList, SharePointUser, SharePointGroup, SharePointFolder


def _mock_response(data: dict, status_code: int = 200) -> Response:
    """Create a minimal ``requests.Response`` object with JSON data."""
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.text = json.dumps(data)
    mock_resp.request = MagicMock()
    mock_resp.request.url = "https://example.com/_api/Web"
    return mock_resp


@pytest.fixture
def mock_session():
    """Provide a mocked ``requests.Session``."""
    return MagicMock(spec=Session)


@pytest.fixture
def site_metadata():
    """Typical site metadata payload returned by SharePoint."""
    return {
        "d": {
            "Title": "Demo Site",
            "Url": "https://example.com/sites/demo",
            "Description": "A demo SharePoint site",
            "Created": "2023-04-01T12:00:00Z",
            "Language": 1033,  # en-US
            "ServerRelativeUrl": "/sites/demo",
            "Lists": {"__deferred": {"uri": "https://example.com/_api/Web/Lists"}},
            "SiteUsers": {"__deferred": {"uri": "https://example.com/_api/Web/SiteUsers"}},
            "SiteGroups": {"__deferred": {"uri": "https://example.com/_api/Web/SiteGroups"}},
            "Folders": {"__deferred": {"uri": "https://example.com/_api/Web/Folders"}},
        }
    }


def test_site_properties(mock_session, site_metadata):
    """Validate basic property access on ``SharePointSite``."""
    mock_session.get.return_value = _mock_response(site_metadata)

    site = SharePointSite(
        site_url="https://example.com/_api/Web",
        session=mock_session,
    )

    # Simple string properties
    assert site.title == "Demo Site"
    assert site.url == "https://example.com/sites/demo"
    assert site.description == "A demo SharePoint site"
    assert site.relative_url == "/sites/demo"

    # ``created`` returns a timezone‑aware ``datetime``
    created = site.created
    assert isinstance(created, datetime)
    assert created.tzinfo is not None
    # The original string is UTC, so the datetime should be UTC
    assert created == datetime(2023, 4, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_get_lists_returns_sharepointlist_instances(mock_session, site_metadata):
    """``get_lists`` should return a list of ``SharePointList`` objects."""
    # First call – site metadata
    mock_session.get.side_effect = [
        _mock_response(site_metadata),  # metadata for the site
        _mock_response(
            {
                "d": {
                    "results": [
                        {
                            "__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list-1')"},
                            "Title": "Tasks",
                        },
                        {
                            "__metadata": {"uri": "https://example.com/_api/Web/Lists(guid'list-2')"},
                            "Title": "Documents",
                        },
                    ]
                }
            }
        ),  # response for the Lists endpoint
    ]

    site = SharePointSite(
        site_url="https://example.com/_api/Web",
        session=mock_session,
    )

    lists = site.get_lists()
    assert isinstance(lists, list)
    assert len(lists) == 2
    assert all(isinstance(l, SharePointList) for l in lists)

    # Verify that the underlying URLs are correctly passed to the ``SharePointList`` ctor
    assert lists[0].list_url == "https://example.com/_api/Web/Lists(guid'list-1')"
    assert lists[1].list_url == "https://example.com/_api/Web/Lists(guid'list-2')"


def test_get_user_returns_sharepointuser_instance(mock_session, site_metadata):
    """``get_user`` should return a ``SharePointUser`` with the correct endpoint."""
    mock_session.get.return_value = _mock_response(site_metadata)

    site = SharePointSite(
        site_url="https://example.com/_api/Web",
        session=mock_session,
    )

    user = site.get_user(user_id=42)
    expected_url = "https://example.com/_api/Web/GetUserById(42)"
    assert isinstance(user, SharePointUser)
    assert user.site_user_url == expected_url


def test_get_group_returns_sharepointgroup_instance(mock_session, site_metadata):
    """``get_group`` should return a ``SharePointGroup`` with the correct endpoint."""
    mock_session.get.return_value = _mock_response(site_metadata)

    site = SharePointSite(
        site_url="https://example.com/_api/Web",
        session=mock_session,
    )

    group = site.get_group(group_name="Project Managers")
    expected_url = "https://example.com/_api/Web/SiteGroups/GetByName('Project Managers')"
    assert isinstance(group, SharePointGroup)
    assert group.group_url == expected_url


def test_get_folder_returns_sharepointfolder_instance(mock_session, site_metadata):
    """``get_folder`` should return a ``SharePointFolder`` with the correct endpoint."""
    mock_session.get.return_value = _mock_response(site_metadata)

    site = SharePointSite(
        site_url="https://example.com/_api/Web",
        session=mock_session,
    )

    folder = site.get_folder(folder_name="Shared Documents")
    expected_url = "https://example.com/_api/Web/GetFolderByServerRelativeUrl('Shared Documents')"
    assert isinstance(folder, SharePointFolder)
    assert folder.folder_url == expected_url