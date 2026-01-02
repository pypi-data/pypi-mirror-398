from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore
from plexflow.core.context.plexflow_context import PlexflowContext
from plexflow.core.context.plexflow_property import PlexflowObjectProperty
from plexflow.core.plex.watchlist.datatypes import PlexMetadata
from typing import Union

class SelectContext(PlexflowContext):
    """A class used to represent a Select Context in Plexflow.

    This class extends PlexflowContext and adds a selected item property.

    Attributes:
        selected_item (PlexflowObjectProperty): The selected item in the context.
    """

    def __init__(self, store: PlexflowObjectStore, **kwargs):
        """Initializes the SelectContext with the given object store and keyword arguments.

        Args:
            store (PlexflowObjectStore): The object store to be used.
            **kwargs: Arbitrary keyword arguments.
        """

        super().__init__(store=store, **kwargs)
        self.selected_item = PlexflowObjectProperty(self.object_store, "selected", local=True)

    @property
    def item(self) -> Union[PlexMetadata, None]:
        """Gets the value of the selected item.

        Returns:
            Any: The value of the selected item.
        """

        return self.selected_item.value
    
    @item.setter
    def item(self, val: PlexMetadata):
        """Sets the value of the selected item.

        Args:
            val (Any): The value to be set.
        """

        self.selected_item.value = val
