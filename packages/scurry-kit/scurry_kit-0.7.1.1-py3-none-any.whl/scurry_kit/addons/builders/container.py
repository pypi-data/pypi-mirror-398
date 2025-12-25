from scurrypy import (
    Addon,
    Separator, SeparatorTypes
)

class ContainerBuilder(Addon):
    """Common Container Helpers."""
    
    @staticmethod
    def small_separator(divider: bool = True):
        """Builds a separator with a small padding.

        Args:
            divider (bool, optional): Whether a visual divider should appear. Defaults to True.

        Returns:
            (Separator): the separator object
        """
        return Separator(divider, SeparatorTypes.SMALL_PADDING)
    
    @staticmethod
    def large_separator(divider: bool = True):
        """Builds a separator with a large padding.

        Args:
            divider (bool, optional): Whether a visual divider should appear. Defaults to True.

        Returns:
            (Separator): the separator object
        """
        return Separator(divider, SeparatorTypes.LARGE_PADDING)
