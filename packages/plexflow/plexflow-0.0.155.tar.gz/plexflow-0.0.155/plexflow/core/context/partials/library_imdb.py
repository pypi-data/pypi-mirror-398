from plexflow.core.context.partial_context import PartialContext

class LibraryIMDb(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def add_movie_ids(self, ids: set):
        self.set_global("library/imdb/movies", ids)
    
    def add_show_ids(self, ids: set):
        self.set_global("library/imdb/shows", ids)
    
    def get_movie_ids(self) -> set:
        try:
            return self.get_global("library/imdb/movies")
        except:
            return set()

    def get_show_ids(self) -> set:
        try:
            return self.get_global("library/imdb/shows")
        except:
            return set()