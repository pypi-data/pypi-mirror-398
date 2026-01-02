from plexflow.core.context.plexflow_context import PlexflowContext
from plexflow.core.context.select.context import SelectContext
from plexflow.core.context.watchlist.context import WatchlistContext
from plexflow.core.context.metadata.context import MetadataContext
from plexflow.core.context.torrent.context import TorrentContext

class RootContext(PlexflowContext):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def select(self):
        return SelectContext(self.object_store)
    
    @property
    def watchlist(self):
        return WatchlistContext(self.object_store)
    
    @property
    def metadata(self):
        return MetadataContext(self.object_store)
    
    @property
    def torrent(self):
        return TorrentContext(self.object_store)