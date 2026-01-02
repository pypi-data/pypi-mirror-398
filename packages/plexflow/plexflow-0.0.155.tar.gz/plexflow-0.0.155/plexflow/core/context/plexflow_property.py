from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore

class PlexflowObjectProperty:
    """A class used to represent a property of a Plexflow object."""

    def __init__(self, store: PlexflowObjectStore, key: str, local: bool = True):
        """Initializes the PlexflowObjectProperty with the given object store, key, and locality.

        Args:
            store (PlexflowObjectStore): The object store to be used.
            key (str): The key of the object.
            local (bool, optional): Whether the key is local. Defaults to True.
        """

        self.store = store
        self.object_key = self.store.make_run_key(key) if local else self.store.make_key(key)

    @property
    def value(self):
        """Gets the value of the object from the object store.

        Returns:
            Any: The value of the object.
        """

        return self.store.retrieve(self.object_key)
    
    @value.setter
    def value(self, val):
        """Sets the value of the object in the object store.

        Args:
            val (Any): The value to be set.
        """

        self.store.store_temporarily(self.object_key, val)
