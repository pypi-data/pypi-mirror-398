from plexflow.core.plex.api.context.discover import PlexDiscoverRequestContext

def add_to_watchlist(rating_key: str):
    context = PlexDiscoverRequestContext()
    response = context.put(f'/actions/addToWatchlist?ratingKey={rating_key}')
    response.raise_for_status()
    return response.json()

def remove_from_watchlist(rating_key: str):
    context = PlexDiscoverRequestContext()
    response = context.put(f'/actions/removeFromWatchlist?ratingKey={rating_key}')
    response.raise_for_status()
    return response.json()