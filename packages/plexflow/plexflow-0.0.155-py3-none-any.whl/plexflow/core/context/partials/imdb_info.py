from plexflow.core.context.partial_context import PartialContext

class IMDbInfo(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def add_persisted_query_hash(self, hash: str):
        self.set_global("imdb/persisted_query_hash", hash)
    
    def get_persisted_query_hash(self) -> str:
        try:
            return self.get_global("imdb/persisted_query_hash")
        except:
            return None

    def add_end_cursor(self, cursor: str):
        self.set_global("imdb/end_cursor", cursor)
    
    def get_end_cursor(self) -> str:
        try:
            return self.get_global("imdb/end_cursor")
        except:
            return None
    
    def add_most_popular_count(self, count: int):
        self.set_global("imdb/most_popular_count", count)

    def get_most_popular_count(self) -> int:
        try:
            return self.get_global("imdb/most_popular_count")
        except:
            return 0