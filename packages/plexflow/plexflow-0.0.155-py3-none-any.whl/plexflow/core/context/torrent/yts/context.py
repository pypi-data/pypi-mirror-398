from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore
from plexflow.core.context.plexflow_context import PlexflowContext
from plexflow.core.context.plexflow_property import PlexflowObjectProperty
from plexflow.core.torrents.providers.yts.utils import YTSSearchResult
from typing import Union, List

class YTSTorrentContext(PlexflowContext):
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
        self._torrents = PlexflowObjectProperty(self.object_store, "torrents", local=True)

    @property
    def items(self) -> Union[List[YTSSearchResult], None]:
        """Gets the value of the selected item.

        Returns:
            Any: The value of the selected item.
        """

        return self._torrents.value
    
    @items.setter
    def items(self, val: List[YTSSearchResult]):
        """Sets the value of the selected item.

        Args:
            val (Any): The value to be set.
        """

        self._torrents.value = val
