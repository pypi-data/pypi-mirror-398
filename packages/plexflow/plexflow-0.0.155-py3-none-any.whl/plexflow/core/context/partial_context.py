from plexflow.core.storage.object.plexflow_storage import PlexflowObjectStore
from typing import Any
from ulid import ULID

class PartialContext:
    @staticmethod
    def create_universal_id(dag_run_id: str):
        store = PlexflowObjectStore(dag_run_id)
        try:
            print("try retrieving universal id")
            universal_id = store.retrieve(store.make_key(dag_run_id))
            if isinstance(universal_id, str) and len(universal_id) > 0:
                return universal_id
        except Exception:
            print("creating universal id")
            
        universal_id = str(ULID())
        store.store_temporarily(key=store.make_key(dag_run_id), obj=universal_id)
        return universal_id
    
    @staticmethod
    def update_custom(context_id: str, key: str, value: Any, ttl: int = None):
        ctx = PartialContext(
            context_id=context_id,
            dag_run_id=f"CUSTOM_{context_id}",
            default_ttl=ttl,
        )

        ctx.set(key, value, ttl=ttl)

    def __init__(self, context_id: str, dag_run_id: str, default_ttl: int, **kwargs) -> None:
        self.context_id = context_id
        self.dag_run_id = dag_run_id
        self.default_ttl = default_ttl
        self.store = PlexflowObjectStore(context_id, **kwargs)
    
    def update_universal_id(self, value: str):
        self.store.store_temporarily(key=self.store.make_key(self.dag_run_id), obj=value)

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        self.store.store_temporarily(key=self.store.make_run_key(key), obj=value, ttl=ttl or self.default_ttl)

    def set_global(self, key: str, value: Any, ttl: int = None) -> None:
        self.store.store_temporarily(key=self.store.make_key(key), obj=value, ttl=ttl or self.default_ttl)
    
    def get(self, key: str) -> Any:
        return self.store.retrieve(key=self.store.make_run_key(key))

    def get_global(self, key: str) -> Any:
        return self.store.retrieve(key=self.store.make_key(key))

    def get_keys(self, pattern: str):
        return list(map(lambda key_bytes: key_bytes.decode('utf-8'), self.store.retrieve_keys(self.store.make_run_key(pattern))))
    
    def get_by_pattern(self, pattern: str):
        return self.store.retrieve_values(self.store.make_run_key(pattern))
