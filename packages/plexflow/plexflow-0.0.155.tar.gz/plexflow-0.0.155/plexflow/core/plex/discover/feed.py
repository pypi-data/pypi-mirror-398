from typing import List
from plexflow.core.plex.hooks.plex_authorized import PlexAuthorizedHttpHook
from plexflow.core.plex.discover.activity import Activity, get_activities

class ActivityFeed:
    def __init__(self):
        pass
    
    @property
    def activities(self) -> List[Activity]:
        return get_activities(total=100)