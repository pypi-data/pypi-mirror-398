from plexflow.core.plex.api.context.discover import PlexDiscoverRequestContext

def get_most_watchlisted():
    context = PlexDiscoverRequestContext()
    response = context.get('/hubs/sections/home/top_watchlisted')
    response.raise_for_status()
    data = response.json()    
    metadata = data["MediaContainer"]['Metadata']
    return metadata

def get_coming_soon():
    context = PlexDiscoverRequestContext()
    response = context.get('/hubs/sections/home/coming-soon')
    response.raise_for_status()
    data = response.json()
    metadata = data["MediaContainer"]['Metadata']
    return metadata

def get_higly_anticipated():
    context = PlexDiscoverRequestContext()
    response = context.get('/hubs/sections/home/highly-anticipated-movies')
    response.raise_for_status()
    data = response.json()
    metadata = data["MediaContainer"]['Metadata']
    return metadata

def get_upcoming_blockbusters():
    context = PlexDiscoverRequestContext()
    response = context.get('/hubs/sections/home/blockbuster-trailers')
    response.raise_for_status()
    data = response.json()
    metadata = data["MediaContainer"]['Metadata']
    return metadata