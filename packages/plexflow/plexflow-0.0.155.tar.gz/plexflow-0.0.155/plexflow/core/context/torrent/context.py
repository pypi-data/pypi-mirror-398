from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore
from plexflow.core.context.plexflow_context import PlexflowContext
from plexflow.core.context.torrent.tpb.context import ThePirateBayTorrentContext
from plexflow.core.context.torrent.yts.context import YTSTorrentContext

class TorrentContext(PlexflowContext):
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

    @property
    def tpb(self) -> ThePirateBayTorrentContext:
        """Gets the value of the selected item.

        Returns:
            Any: The value of the selected item.
        """

        return ThePirateBayTorrentContext(store=self.object_store)

    @property
    def yts(self) -> YTSTorrentContext:
        """Gets the value of the selected item.

        Returns:
            Any: The value of the selected item.
        """

        return YTSTorrentContext(store=self.object_store)
