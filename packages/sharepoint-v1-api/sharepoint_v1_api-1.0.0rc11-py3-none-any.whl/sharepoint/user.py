from __future__ import annotations
import requests
from ._base import SharePointBase
from typing import Optional


from sharepoint._api import SharePointAPI
from os import path


class SharePointUser(SharePointBase):
    """
    Represents a SharePoint user.
    """

    @classmethod
    def from_relative_url(
        cls,
        base_sharepoint_url: str,
        relative_url: str,
        session: requests.Session,
    ) -> "SharePointUser":
        """
        Initialise a :class:`SharePointUser` using a base SharePoint URL and a
        server‑relative URL.

        Parameters
        ----------
        base_sharepoint_url : str
            The root URL of the SharePoint tenant (e.g. ``https://example.com``).
        relative_url : str
            The server‑relative path to the user endpoint (e.g. ``/sites/demo/_api/Web/siteusers(1)``).
        session : requests.Session
            A pre‑configured session with authentication.

        Returns
        -------
        SharePointUser
            An instance configured with the combined user URL.
        """
        _url = path.join(base_sharepoint_url, relative_url)
        return cls(_url, session)

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def id(self) -> Optional[int]:
        """User identifier."""
        return self.get("Id")

    @property
    def title(self) -> Optional[str]:
        """User display name."""
        return self.get("Title")

    @property
    def email(self) -> Optional[str]:
        """User email address."""
        return self.get("Email")

    @property
    def username(self) -> Optional[str]:
        """User name derived from the email address."""
        if not self._ensure_metadata():
            return None
        email = self.get("Email")
        return email.split("@")[0].lower() if email else None
