"""
client for SharePoint site operations.
"""
import locale
import requests
from datetime import datetime
from typing import List, Optional
from os import path

from ._odata_utils import build_query_url
from ._base import SharePointBase
from .list import SharePointList
from .group import SharePointGroup
from .user import SharePointUser
from .folder import SharePointFolder


class SharePointSite(SharePointBase):
    """
    High-level client representing a SharePoint site.
    """

    @classmethod
    def from_relative_url(
        cls,
        base_sharepoint_url: str,
        relative_url: str,
        session: requests.Session,
    ) -> "SharePointSite":
        """
        Initialise a :class:`SharePointSite` using a base SharePoint URL and a
        server‑relative URL.

        Parameters
        ----------
        base_sharepoint_url : str
            The root URL of the SharePoint tenant (e.g. ``https://example.com``).
        relative_url : str
            The server‑relative path to the site (e.g. ``/sites/demo``).
        session : requests.Session
            A pre‑configured session with authentication.

        Returns
        -------
        SharePointSite
            An instance configured with the combined site URL.
        """
        _url = path.join(
            base_sharepoint_url,
            relative_url,
            "_api/Web",
        )
        return cls(url=_url, session=session)

    # -----------------------------------------------------------------
    # Exposed properties (lazy-loaded)
    # -----------------------------------------------------------------
    @property
    def title(self) -> str:
        """Site title."""
        return self.get("Title", "")

    @property
    def url(self) -> str:
        """Absolute URL of the site."""
        return self.get("Url", "")

    @property
    def description(self) -> str:
        """Site description, if present."""
        return self.get("Description", "")

    @property
    def language_id(self) -> int:
        """Raw LCID value returned by SharePoint."""
        return self.get("Language", 0)

    @property
    def language_name(self) -> str:
        """Human-readable language name derived from the LCID."""
        lcid = self.language_id
        locale_code = locale.windows_locale.get(lcid)
        if not locale_code:
            return f"Unknown (LCID={lcid})"
        try:
            locale.setlocale(locale.LC_ALL, locale_code)
            loc = locale.getlocale()[0]
            if loc:
                return loc
        except locale.Error:
            pass
        return locale_code

    @property
    def relative_url(self) -> str:
        """Server‑relative URL of the site."""
        return self.get('ServerRelativeUrl')

    # -----------------------------------------------------------------
    # Convenience wrappers delegating to the thin client
    # -----------------------------------------------------------------
    def get_lists(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None
    ) -> List[SharePointList]:
        """Return a collection of lists for this site."""

        # Ensure metadata is loaded before accessing it
        list_url = build_query_url(
            self.get('Lists', {}).get(
                '__deferred', {}).get('uri'),
            filters=filters,
            select_fields=select_fields if select_fields else ["__metadata"],
            top=top
        )

        r = self._api.get(list_url)
        return [SharePointList(sp_list.get('__metadata', {}).get(
            "uri"), self._api.session) for sp_list in r.json()["d"]["results"]]

    def get_list(
        self,
        list_guid: str | None = None,
        list_title: str | None = None,
    ) -> SharePointList:
        """Return a :class:`SharePointList` for this site.

        Exactly **one** of ``list_guid`` or ``list_title`` must be supplied.
        ``list_guid`` should be the GUID string (e.g. ``'1234-ABCD-...'``),
        while ``list_title`` is the human-readable list name.

        Raises
        ------
        ValueError
            If both arguments are provided or if neither is provided.
        """
        # ---- exclusive-or validation -----------------------------------------
        if (list_guid is None) == (list_title is None):  # both None or both set
            raise ValueError(
                "Provide **either** `list_guid` **or** `list_title`, "
                "but not both."
            )

        # ---- build the appropriate endpoint ------------------------------------
        if list_guid:
            site_list_url = path.join(
                self._url, f"Lists(guid'{list_guid}')"
            )
        else:  # list_title is guaranteed to be not-None here
            site_list_url = path.join(
                self._url, f"Lists/GetByTitle('{list_title}')"
            )

        # ---- return the wrapper object -----------------------------------------
        return SharePointList(site_list_url, self._api.session)

    def get_users(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None,
    ) -> List[SharePointUser]:
        """Retrieve users from the site."""
        url = self.get(
            'SiteUsers').get('__deferred').get('uri')
        url = build_query_url(
            url,
            filters=filters,
            select_fields=select_fields if select_fields else ["__metadata"],
            top=top
        )
        r = self._api.get(url)

        return [SharePointUser(site_user.get('__metadata', {}).get(
            "uri"), self._api.session) for site_user in r.json()["d"]["results"]]

    def get_user(
        self,
        user_id: int
    ) -> SharePointUser:
        """
        Return a ``SharePointUser`` instance for the given user ID.
        """

        url = path.join(self._url, f"GetUserById({user_id})")

        return SharePointUser(
            url=url,
            session=self._api.session
        )

    def get_groups(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None,
    ) -> List[SharePointGroup]:
        """Retrieve members of a SharePoint group."""

        url = build_query_url(
            self._metadata.get('SiteGroups', {}).get(
                '__deferred', {}).get('uri'),
            filters=filters,
            select_fields=select_fields if select_fields else ["__metadata"],
            top=top
        )

        r = self._api.get(url)
        return [SharePointGroup(sp_list.get('__metadata', {}).get(
            "uri"), self._api.session) for sp_list in r.json()["d"]["results"]]

    def get_group(
        self,
        group_guid: str | None = None,
        group_name: str | None = None,
    ) -> SharePointGroup:
        """Return a :class:`SharePointGroup` for this site.

        Exactly **one** of ``group_guid`` or ``group_name`` must be supplied.
        ``group_guid`` should be the GUID string (e.g. ``'1234-ABCD-...'``),
        while ``group_name`` is the human-readable SharePoint group name.

        Raises
        ------
        ValueError
            If both arguments are provided or if neither is provided.
        """
        # ---- exclusive-or validation -----------------------------------------
        if (group_guid is None) == (group_name is None):
            raise ValueError(
                "Provide **either** `group_guid` **or** `group_name`, "
                "but not both."
            )

        # ---- build the appropriate endpoint ------------------------------------
        if group_guid:
            url = path.join(
                self._url, f"SiteGroups/GetById('{group_guid}')"
            )
        else:  # group_name is guaranteed to be not-None here
            url = path.join(
                self._url, f"SiteGroups/GetByName('{group_name}')"
            )

        # ---- return the wrapper object -----------------------------------------
        return SharePointGroup(url, self._api.session)

    def get_folders(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None
    ) -> List[SharePointFolder]:
        """Return a collection of folders for this site."""

        url = build_query_url(
            self.get('Folders', {}).get(
                '__deferred', {}).get('uri'),
            filters=filters,
            select_fields=select_fields if select_fields else ["__metadata"],
            top=top
        )

        r = self._api.get(url)
        return [
            SharePointFolder(
                sp_list.get('__metadata', {}).get("uri"),
                self._api.session
            )
            for sp_list in r.json()["d"]["results"]
        ]

    def get_folder(
        self,
        folder_guid: str | None = None,
        folder_name: str | None = None,
    ) -> SharePointFolder:
        """Return a :class:`SharePointFolder` for this site.

        Exactly **one** of ``folder_guid`` or ``folder_name`` must be supplied.
        ``folder_guid`` should be the GUID string (e.g. ``'1234-ABCD-...'``),
        while ``folder_name`` is the human-readable folder name.

        Raises
        ------
        ValueError
            If both arguments are provided or if neither is provided.
        """
        # ---- exclusive-or validation -----------------------------------------
        if (folder_guid is None) == (folder_name is None):
            raise ValueError(
                "Provide **either** `folder_guid` **or** `folder_name`, "
                "but not both."
            )

        # ---- build the appropriate endpoint ------------------------------------
        if folder_guid:
            # Retrieve folder by GUID using the documented Web method
            url = path.join(
                self._url, f"GetFolderById(guid'{folder_guid}')"
            )
        else:
            # Retrieve folder by its server-relative URL as per SharePoint REST API
            url = path.join(
                self._url, f"GetFolderByServerRelativeUrl('{folder_name}')"
            )

        # ---- return the wrapper object -----------------------------------------
        return SharePointFolder(url, self._api.session)
