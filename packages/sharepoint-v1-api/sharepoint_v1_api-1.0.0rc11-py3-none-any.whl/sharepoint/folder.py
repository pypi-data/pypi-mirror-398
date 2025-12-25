from typing import List, Optional, Self
import requests
import datetime
from os import path
from ._api import SharePointAPI
from ._odata_utils import build_query_url
from ._base import SharePointBase


class SharePointFolder(SharePointBase):
    """
    Base class representing a SharePoint folder.

    Provides common functionality for handling folder items, including
    retrieval, addition, and serialization to JSON. Subclasses such as
    :class:`Casesfolder` and :class:`TimeRegistrationfolder` extend this
    class with domain-specific behavior.
    """

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def name(self) -> str:
        """Folder name."""
        return self.get('Name')

    @property
    def id(self) -> str:
        """Unique identifier of the folder."""
        return self.get('UniqueId')

    @property
    def relative_url(self) -> str:
        """Server‑relative URL of the folder."""
        return self.get('ServerRelativeUrl')

    @property
    def created(self) -> Optional[datetime.datetime]:
        """Timestamp when the item was created."""
        return self.get_datetime("TimeCreated")

    @property
    def modified(self) -> Optional[datetime.datetime]:
        """Timestamp when the item was last modified."""
        return self.get_datetime("TimeLastModified")

    def get_folders(
        self,
        filters: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = None
    ) -> List[Self]:
        """Return a collection of folders for this site."""

        url = build_query_url(
            self.get('Folders', {}).get(
                '__deferred', {}).get('uri'),
            filters=filters,
            select_fields=select_fields if select_fields else ["__metadata"],
            top=top
        )

        r = self._api.get(url)
        # Use the same class (including subclasses) for each returned folder.
        # ``self.__class__`` ensures that if this method is called on a subclass,
        # the instances created are of that subclass, preserving any overridden
        # behaviour.  Pass the existing session so the new objects share the
        # authenticated session.
        return [
            SharePointFolder(
                sp_item.get('__metadata', {}).get("uri"),
                self._api.session,
            )
            for sp_item in r.json()["d"]["results"]
        ]

    def get_folder(
        self,
        folder_guid: str | None = None,
        folder_name: str | None = None,
    ) -> Self:
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
