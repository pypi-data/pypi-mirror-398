from __future__ import annotations
from os import path
from datetime import datetime
from typing import Optional
from ._base import SharePointBase


class SharePointListItemVersion(SharePointBase):
    """
    Represents a generic version of a SharePoint list item.
    """

    @property
    def _update_metadata(self) -> dict:
        """Fetch list item version metadata on first use and cache it."""
        r = self._api.get(self._url)
        self._metadata = r.json().get("d", {})

    @property
    def _form_digestive_value(self):
        r = self._api.post(
            path.join(
                self.base_url,
                '_api/contextinfo'
            ), {})

        return r.json()["d"]["GetContextWebInformation"]["FormDigestValue"]

    @property
    def id(self) -> Optional[str]:
        """The unique version id"""
        return self.get("VersionId")

    @property
    def version_label(self) -> Optional[str]:
        """The version label."""
        return self.get("VersionLabel")

    @property
    def title(self) -> Optional[str]:
        """Title of the list item."""
        return self.get("Title")

    @property
    def modified(self) -> Optional[datetime]:
        """Timestamp when the item was last modified."""
        return self.get_datetime("Modified")
