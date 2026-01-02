import os
from typing import Generator, Tuple

def search_files(directory: str, extensions: Tuple[str, ...], order_by_size: bool = False, ignore_hidden: bool = True) -> Generator[str, None, None]:
    """
    Generator function to search for files in a directory recursively. If extensions are specified, 
    only files with those extensions are returned. If no extensions are specified, all files are returned.
    Optionally order the files by size and/or ignore hidden files.

    Parameters:
    directory (str): The directory in which to start the search.
    extensions (tuple of str): The file extensions to search for. If empty, all files are returned.
    order_by_size (bool, optional): Whether to order the files by size. Default is False.
    ignore_hidden (bool, optional): Whether to ignore hidden files. Default is True.

    Yields:
    str: The path to a file that matches one of the specified extensions, or any file if no extensions are specified.

    Examples:
    >>> # Search for Python and text files, ordered by size, including hidden files
    >>> for file in search_files('/path/to/directory', ('.txt', '.py'), order_by_size=True, ignore_hidden=False):
    ...     print(file)

    >>> # Search for JPEG and PNG images, not ordered by size, ignoring hidden files
    >>> for file in search_files('/path/to/directory', ('.jpg', '.png')):
    ...     print(file)

    >>> # Search for Markdown files, ordered by size, ignoring hidden files
    >>> for file in search_files('/path/to/directory', ('.md',), order_by_size=True):
    ...     print(file)

    >>> # Search for all files, not ordered by size, ignoring hidden files
    >>> for file in search_files('/path/to/directory', (), order_by_size=False, ignore_hidden=True):
    ...     print(file)
    """

    # Gather all files first if ordering by size
    if order_by_size:
        files = []
        for dirpath, dirnames, filenames in os.walk(directory):
            if ignore_hidden:
                filenames = [f for f in filenames if not f[0] == '.']
                dirnames[:] = [d for d in dirnames if not d[0] == '.']
            for filename in filenames:
                if not extensions or filename.endswith(extensions):
                    filepath = os.path.join(dirpath, filename)
                    files.append((os.path.getsize(filepath), filepath))
        files.sort(reverse=True)  # Files are now sorted by size in decreasing order
        for _, filepath in files:
            yield filepath
    else:
        # Original behavior, yield files as they are found
        for dirpath, dirnames, filenames in os.walk(directory):
            if ignore_hidden:
                filenames = [f for f in filenames if not f[0] == '.']
                dirnames[:] = [d for d in dirnames if not d[0] == '.']
            for filename in filenames:
                if not extensions or filename.endswith(extensions):
                    yield os.path.join(dirpath, filename)


def find_movie_files(directory: str, extensions: Tuple[str, ...] = ('.mp4', '.mkv', '.avi', '.mov', '.flv'), order_by_size: bool = False, ignore_hidden: bool = True) -> Generator[str, None, None]:
    """
    Generator function to search for movie files in a directory recursively. 
    Movie files are considered to have the extensions: '.mp4', '.mkv', '.avi', '.mov', '.flv', unless specified otherwise.
    Optionally order the files by size and/or ignore hidden files.

    Parameters:
    directory (str): The directory in which to start the search.
    extensions (tuple of str, optional): The file extensions to search for. Default is ('.mp4', '.mkv', '.avi', '.mov', '.flv').
    order_by_size (bool, optional): Whether to order the files by size. Default is False.
    ignore_hidden (bool, optional): Whether to ignore hidden files. Default is True.

    Yields:
    str: The path to a movie file.

    Examples:
    >>> # Search for movie files, ordered by size, including hidden files
    >>> for file in find_movie_files('/path/to/directory', order_by_size=True, ignore_hidden=False):
    ...     print(file)

    >>> # Search for movie files, not ordered by size, ignoring hidden files
    >>> for file in find_movie_files('/path/to/directory'):
    ...     print(file)

    >>> # Search for movie files, ordered by size, ignoring hidden files
    >>> for file in find_movie_files('/path/to/directory', order_by_size=True):
    ...     print(file)

    >>> # Search for custom file types
    >>> for file in find_movie_files('/path/to/directory', extensions=('.wmv', '.mpg')):
    ...     print(file)
    """
    return search_files(directory, extensions, order_by_size, ignore_hidden)


def find_subtitle_files(directory: str, extensions: Tuple[str, ...] = ('.srt', '.sub', '.sbv', '.vtt', '.ass'), order_by_size: bool = False, ignore_hidden: bool = True) -> Generator[str, None, None]:
    """
    Generator function to search for subtitle files in a directory recursively. 
    Subtitle files are considered to have the extensions: '.srt', '.sub', '.sbv', '.vtt', '.ass', unless specified otherwise.
    Optionally order the files by size and/or ignore hidden files.

    Parameters:
    directory (str): The directory in which to start the search.
    extensions (tuple of str, optional): The file extensions to search for. Default is ('.srt', '.sub', '.sbv', '.vtt', '.ass').
    order_by_size (bool, optional): Whether to order the files by size. Default is False.
    ignore_hidden (bool, optional): Whether to ignore hidden files. Default is True.

    Yields:
    str: The path to a subtitle file.

    Examples:
    >>> # Search for subtitle files, ordered by size, including hidden files
    >>> for file in find_subtitle_files('/path/to/directory', order_by_size=True, ignore_hidden=False):
    ...     print(file)

    >>> # Search for subtitle files, not ordered by size, ignoring hidden files
    >>> for file in find_subtitle_files('/path/to/directory'):
    ...     print(file)

    >>> # Search for subtitle files, ordered by size, ignoring hidden files
    >>> for file in find_subtitle_files('/path/to/directory', order_by_size=True):
    ...     print(file)

    >>> # Search for custom file types
    >>> for file in find_subtitle_files('/path/to/directory', extensions=('.smi', '.ssa')):
    ...     print(file)
    """
    return search_files(directory, extensions, order_by_size, ignore_hidden)
