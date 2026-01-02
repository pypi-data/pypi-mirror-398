from typing import Optional, Dict, Any
from plexflow.utils.hooks.postgresql import UniversalPostgresqlHook

class PlexflowDatabase(UniversalPostgresqlHook):
    def __init__(self, postgres_conn_id: Optional[str] = None, config_folder: Optional[str] = None):
        super().__init__(postgres_conn_id, config_folder)
