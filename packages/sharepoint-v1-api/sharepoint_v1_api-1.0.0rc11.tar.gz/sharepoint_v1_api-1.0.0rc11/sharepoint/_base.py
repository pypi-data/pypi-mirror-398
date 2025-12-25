"""
Base utilities for SharePoint objects.

Provides common functionality for handling metadata retrieval and merging.
All high‑level SharePoint objects (Site, Folder, Group, List, ListItem,
ListField, User) should inherit from :class:`SharePointBase`.
"""

from __future__ import annotations

import requests
from typing import List, Optional, Any
from ._datetime_utils import parse_sharepoint_datetime
from datetime import datetime
from ._api import SharePointAPI
from ._odata_utils import build_query_url


class SharePointBase:
    """
    Base class representing a generic SharePoint object.

    Sub‑classes should pass the object's primary URL (e.g. the endpoint used
    for a GET request) to ``super().__init__(url, session)``. The base class
    stores a thin :class:`SharePointAPI` transport client, caches the raw
    metadata dictionary and provides helpers for lazy loading and optional
    OData queries.

    Attributes
    ----------
    _api : SharePointAPI
        Thin transport client used for all HTTP calls.
    _url : str
        Primary endpoint URL for the object (used by ``_ensure_metadata``).
    _metadata : Optional[dict]
        Cached metadata dictionary returned by SharePoint.
    """

    def __init__(self, url: str, session: requests.Session, metadata: dict = None):
        """
        Initialise the base object.

        Parameters
        ----------
        url : str
            The primary endpoint URL for the SharePoint object.
        session : requests.Session
            A pre‑configured session with authentication (NTLM, etc.).
        """
        # Initialise the thin transport client.
        self._api: SharePointAPI = SharePointAPI(session=session)
        self._url: str = url
        self._metadata: Optional[dict] = metadata

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------
    def _ensure_metadata(self) -> dict:
        """Fetch object metadata on first use and cache it."""
        if self._metadata is None:
            r = self._api.get(self._url)
            self._metadata = r.json().get("d", {})
        return self._metadata

    @property
    def _update_metadata(self) -> dict:
        """Fetch site metadata on first use and cache it."""
        r = self._get_metadata()

    def _get_metadata(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None,
    ) -> dict:
        """
        Retrieve metadata using an optional OData query and merge it into the
        cached ``_metadata`` dictionary.

        Parameters
        ----------
        filters : Optional[str]
            OData ``$filter`` expression.
        select_fields : Optional[List[str]]
            OData ``$select`` fields.
        top : Optional[int]
            OData ``$top`` limit.

        Returns
        -------
        dict
            The updated metadata cache.
        """
        query_url = build_query_url(
            self._url,
            filters=filters,
            select_fields=select_fields,
            top=top,
        )
        r = self._api.get(query_url)
        data = r.json().get("d", {})
        if isinstance(self._metadata, dict):
            self._metadata.update(data)
        else:
            self._metadata = data
        return self._metadata

    def get(self, field_name: str, default: None = None) -> Any:
        """Get a value from the object's metadata, loading it lazily if necessary.

        Parameters
        ----------
        field_name : str
            The metadata field name to retrieve.

        Returns
        -------
        Any
            The value of the requested metadata field, or ``None`` if not present.
        """
        if self._metadata is None or field_name not in self._metadata:
            # Retrieve only the requested field
            self._get_metadata(select_fields=[field_name])
        return self._metadata.get(field_name, default)

    def get_datetime(self, field_name: str, default: None = None) -> datetime | None:
        datetime_str = self.get(field_name, default)
        return parse_sharepoint_datetime(datetime_str, self._api.timezone)

    @property
    def created(self) -> datetime | None:
        """Creation timestamp of the site."""
        return self.get_datetime("Created")
