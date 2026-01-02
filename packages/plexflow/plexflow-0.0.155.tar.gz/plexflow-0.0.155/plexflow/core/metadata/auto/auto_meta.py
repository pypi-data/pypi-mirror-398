from plexflow.core.metadata.auto.auto_providers.auto.movie import AutoMovie
from plexflow.core.metadata.auto.auto_providers.auto.show import AutoShow
from plexflow.core.metadata.auto.auto_providers.tmdb.movie import AutoTmdbMovie
from plexflow.core.metadata.auto.auto_providers.tvdb.movie import AutoTvdbMovie
from plexflow.core.metadata.auto.auto_providers.moviemeter.movie import AutoMovieMeterMovie
from plexflow.core.metadata.auto.auto_providers.imdb.movie import AutoImdbMovie
from plexflow.core.metadata.auto.auto_providers.tmdb.show import AutoTmdbShow
from plexflow.core.metadata.auto.auto_providers.tvdb.show import AutoTvdbShow
from plexflow.core.metadata.auto.auto_providers.imdb.show import AutoImdbShow
from plexflow.core.metadata.auto.auto_providers.plex.show import AutoPlexShow
from plexflow.core.metadata.auto.auto_providers.plex.movie import AutoPlexMovie

class AutoMeta:
    @staticmethod
    def movie(imdb_id: str = None, source: str = 'tmdb', rating_key: str = None) -> AutoMovie:
        if source == 'tmdb':
            return AutoTmdbMovie(imdb_id)
        elif source == 'tvdb':
            return AutoTvdbMovie(imdb_id)
        elif source =='moviemeter':
            return AutoMovieMeterMovie(imdb_id)
        elif source == 'imdb':
            return AutoImdbMovie(imdb_id)
        elif source == "plex":
            if isinstance(rating_key, str):
                return AutoPlexMovie(rating_key)
            else:
                raise ValueError("if source = 'plex', rating_key must be set")
        else:
            raise ValueError(f"Invalid source: {source}")

    @staticmethod
    def show(imdb_id: str = None, source: str = 'tmdb', rating_key: str = None) -> AutoShow:
        if source == 'tmdb':
            return AutoTmdbShow(imdb_id)
        elif source == 'tvdb':
            return AutoTvdbShow(imdb_id)
        elif source == 'imdb':
            return AutoImdbShow(imdb_id)
        elif source == 'plex':
            return AutoPlexShow(rating_key=rating_key)
        else:
            raise ValueError(f"Invalid source: {source}")
