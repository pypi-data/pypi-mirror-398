from __future__ import annotations
from os import path
from typing import Optional
from ._base import SharePointBase


class SharePointListField(SharePointBase):
    """
    Represents a generic field in a SharePoint list.
    """

    _base_url = None

    @property
    def _update_metadata(self) -> dict:
        """Fetch field metadata on first use and cache it."""
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
    def base_url(self) -> str:
        if not self._base_url:
            self._base_url = self._url.split('_api')[0]
        return self._base_url

    @property
    def id(self) -> Optional[str]:
        """Field identifier (GUID)."""
        return self.get("Id")

    @property
    def etag(self) -> Optional[str]:
        """Entity tag of the field."""
        return self.get("__metadata", {}).get('etag')

    @property
    def title(self) -> Optional[str]:
        """Display title of the field."""
        return self.get("Title")

    @property
    def internal_name(self) -> Optional[str]:
        """Internal name of the field."""
        return self.get("InternalName")

    @property
    def static_name(self) -> Optional[str]:
        """Static name of the field."""
        return self.get("StaticName")

    @property
    def type_as_string(self) -> Optional[str]:
        """Field type as string."""
        return self.get("TypeAsString")

    @property
    def type_display_name(self) -> Optional[str]:
        """Human‑readable field type."""
        return self.get("TypeDisplayName")

    @property
    def required(self) -> bool:
        """Whether the field is required."""
        return bool(self.get("Required"))

    @property
    def hidden(self) -> bool:
        """Whether the field is hidden."""
        return bool(self.get("Hidden"))

    @property
    def read_only(self) -> bool:
        """Whether the field is read‑only."""
        return bool(self.get("ReadOnlyField"))

    def update_field(self, data) -> None:
        '''
            Update a SharePoint field

            _url: The URL of the field to update
            data: Dictionary of fields to update
        '''
        r = self._api.post(
            self._url,
            data,
            self._form_digestive_value,
            merge=True)
        self._update_metadata
        return r.ok

    def delete_field(self) -> bool:
        """
        Delete the SharePoint list field.

        Returns True if the deletion succeeded, False otherwise.
        """
        r = self._api.post_complex(
            self._url,
            post_data=None,
            form_digest_value=self._form_digestive_value,
            x_http_method='DELETE')
        return r.ok
