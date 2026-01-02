from plexflow.core.context.partial_context import PartialContext
from datetime import datetime as dt
    
class LRUCache(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def touch(self, media_id: str) -> None:
        self.set_global(f"cache/processing/{media_id}", dt.now())
    
    def last_used(self, media_id: str) -> dt:
        try:
            return self.get_global(f"cache/processing/{media_id}")
        except Exception:
            return None

