from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore
from plexflow.core.context.plexflow_context import PlexflowContext
from plexflow.core.context.metadata.tmdb.context import TMDbMetadataContext

class MetadataContext(PlexflowContext):
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
    def tmdb(self) -> TMDbMetadataContext:
        """Gets the value of the selected item.

        Returns:
            Any: The value of the selected item.
        """

        return TMDbMetadataContext(store=self.object_store)
