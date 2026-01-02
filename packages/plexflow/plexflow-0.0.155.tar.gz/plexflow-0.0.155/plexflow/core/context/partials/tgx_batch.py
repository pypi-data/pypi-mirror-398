from plexflow.core.context.partial_context import PartialContext

class TgxBatch(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def update(self, ids):
        self.set("tgx/ids", ids)
    
    def update_finished(self, ids):
        self.set("tgx/finished", ids)
    
    def update_unfinished(self, ids):
        self.set("tgx/unfinished", ids)
    
    def update_finished_items(self, items):
        self.set("tgx/finished_items", items)
    
    @property
    def ids(self) -> set:
        return self.get("tgx/ids")
    
    @property
    def finished(self) -> set:
        return self.get("tgx/finished")
    
    @property
    def unfinished(self) -> set:
        return self.get("tgx/unfinished")
    
    @property
    def finished_items(self) -> list:
        return self.get("tgx/finished_items")