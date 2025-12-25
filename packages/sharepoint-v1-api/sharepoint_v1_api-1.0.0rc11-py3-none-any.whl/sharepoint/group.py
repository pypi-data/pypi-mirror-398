from ._base import SharePointBase



class SharePointGroup(SharePointBase):
    """
    Base class representing a SharePoint group.

    Provides common functionality for handling groups.
    """

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def title(self) -> str:
        """Group title."""
        return self.get('Title')

    @property
    def guid(self) -> str:
        return self.get('Id')

    # TODO get users method
