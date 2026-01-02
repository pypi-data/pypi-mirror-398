from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore
from plexflow.core.context.plexflow_context import PlexflowContext
from plexflow.core.context.plexflow_property import PlexflowObjectProperty
from plexflow.core.plex.watchlist.datatypes import MediaContainer
from typing import Union

class WatchlistContext(PlexflowContext):
    """
    A class used to represent a context for managing a watchlist in Plexflow.

    This class extends PlexflowContext and adds a property for the watchlist.

    Attributes:
        watchlist (PlexflowObjectProperty): The watchlist in the context.
    """

    def __init__(self, store: PlexflowObjectStore, **kwargs):
        """
        Initializes the WatchlistContext with the given object store and optional keyword arguments.

        Args:
            store (PlexflowObjectStore): The object store to be used.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(store=store, **kwargs)
        self.watchlist = PlexflowObjectProperty(self.object_store, "watchlist", local=True)

    @property
    def list(self) -> Union[MediaContainer, None]:
        """
        Gets the value of the watchlist.

        Returns:
            Any: The value of the selected watchlist item.
        """
        return self.watchlist.value
    
    @list.setter
    def list(self, val: MediaContainer):
        """
        Sets the value of the watchlist.

        Args:
            val (Any): The value to be set.
        """
        self.watchlist.value = val
