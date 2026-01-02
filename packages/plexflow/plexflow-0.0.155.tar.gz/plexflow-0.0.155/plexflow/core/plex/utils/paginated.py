from typing import Iterator

def paginated(func) -> Iterator:
    """
    Decorator function that enables paginated retrieval of data from the Plex API.

    Args:
        func: The function to be decorated.

    Yields:
        The partial response obtained from the decorated function.

    Raises:
        Exception: If an error occurs during the retrieval process.

    Returns:
        The wrapper function that enables paginated retrieval.
    """
    def wrapper():
        container_start = 0
        container_size = 100
        container_end_reached = False
        
        while not container_end_reached:
            try:
                partial_response = func(params={
                    "X-Plex-Container-Start": container_start,
                    "X-Plex-Container-Size": container_size,
                })
                
                yield partial_response
                
                if len(partial_response.Metadata) == 0:
                    container_end_reached = True
                
                container_start += container_size
            except Exception as _:
                container_end_reached = True
    return wrapper
