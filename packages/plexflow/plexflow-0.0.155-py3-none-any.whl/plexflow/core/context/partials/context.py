from plexflow.core.context.partial_context import PartialContext

class Context(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def update(self, id: str):
        self.update_universal_id(id)

    @property
    def id(self) -> str:
        return self.context_id
