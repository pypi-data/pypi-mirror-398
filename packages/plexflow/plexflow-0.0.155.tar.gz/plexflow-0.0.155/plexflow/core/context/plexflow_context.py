from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore

class PlexflowContext:
    """A class used to represent the Plexflow Context.

    This class provides a context for Plexflow computations, allowing access to an object store.

    Attributes:
        store (PlexflowObjectStore): The object store used in the Plexflow context.
    """

    def __init__(self, store: PlexflowObjectStore):
        """Initializes the PlexflowContext with the given object store.

        Args:
            store (PlexflowObjectStore): The object store to be used in the Plexflow context.
        """

        self.store = store

    @property
    def object_store(self) -> PlexflowObjectStore:
        """Gets the object store used in the Plexflow context.

        Returns:
            PlexflowObjectStore: The object store used in the Plexflow context.
        """

        return self.store
