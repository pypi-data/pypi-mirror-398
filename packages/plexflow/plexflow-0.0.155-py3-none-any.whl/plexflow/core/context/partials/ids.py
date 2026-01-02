from plexflow.core.context.partial_context import PartialContext

class Ids(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    @property
    def imdb_id(self) -> str:
        return self.get("imdb_id")
    
    @imdb_id.setter
    def imdb_id(self, value: str) -> None:
        self.set("imdb_id", value)
    
    @property
    def tmdb_id(self) -> int:
        return self.get("tmdb_id")
    
    @tmdb_id.setter
    def tmdb_id(self, value: int) -> None:
        self.set("tmdb_id", value)
    
    @property
    def tvdb_id(self) -> int:
        return self.get("tvdb_id")
    
    @tvdb_id.setter
    def tvdb_id(self, value: int) -> None:
        self.set("tvdb_id", value)
    
    @property
    def plex_id(self) -> str:
        return self.get("plex_id")

    @plex_id.setter
    def plex_id(self, value: str) -> None:
        self.set("plex_id", value)