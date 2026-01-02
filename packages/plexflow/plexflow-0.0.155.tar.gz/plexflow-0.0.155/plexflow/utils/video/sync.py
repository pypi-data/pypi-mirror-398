#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import shutil
import subprocess
import sys


# --- Custom Exceptions for Clearer Error Handling ---
class SubSyncError(Exception):
    """Base exception for this tool."""
    pass

class FFSubsyncExecutableError(SubSyncError):
    """Raised when the ffsubsync executable is not found."""
    pass

class FFSubsyncProcessError(SubSyncError):
    """Raised when the ffsubsync process fails."""
    def __init__(self, message, returncode, stdout, stderr):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def synchronize_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str = None,
    ffsubsync_path: str = 'ffsubsync'
) -> str:
    """
    Synchronizes a subtitle file with a video using ffsubsync.

    Args:
        video_path: Path to the reference video file.
        subtitle_path: Path to the subtitle file to synchronize.
        output_path: Path for the synchronized output file. If None, a default
                     is generated next to the input subtitle.
        ffsubsync_path: Path to the ffsubsync executable.

    Returns:
        The path to the successfully created synchronized subtitle file.

    Raises:
        FFSubsyncExecutableError: If ffsubsync or its dependencies are not found.
        FileNotFoundError: If the input video or subtitle files do not exist.
        FFSubsyncProcessError: If the ffsubsync process returns a non-zero exit code.
    """
    # 1. --- Pre-flight Checks ---
    logging.info("Performing pre-flight checks...")
    if not shutil.which(ffsubsync_path):
        raise FFSubsyncExecutableError(
            f"'{ffsubsync_path}' command not found. Please ensure ffsubsync is "
            "installed (pip install ffsubsync) and in your system's PATH."
        )

    for fpath in [video_path, subtitle_path]:
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Input file not found at '{fpath}'")

    # 2. --- Determine Output Path ---
    if output_path is None:
        base, ext = os.path.splitext(subtitle_path)
        output_path = f"{base}_synced{ext}"

    logging.info(f"Reference video: {video_path}")
    logging.info(f"Input subtitle:  {subtitle_path}")
    logging.info(f"Output path:     {output_path}")

    # 3. --- Construct and Run the Command ---
    command = [
        ffsubsync_path,
        video_path,
        "-i", subtitle_path,
        "-o", output_path,
    ]
    logging.debug(f"Executing command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            check=True,  # Raises CalledProcessError on non-zero exit codes
            capture_output=True,
            text=True,
            encoding='utf-8',
        )
        # ffsubsync logs to stderr, so we log it for debug purposes
        logging.debug("ffsubsync process output (stderr):\n%s", result.stderr)

    except subprocess.CalledProcessError as e:
        raise FFSubsyncProcessError(
            "ffsubsync failed during execution.",
            returncode=e.returncode,
            stdout=e.stdout,
            stderr=e.stderr
        ) from e

    logging.info(f"Successfully synchronized subtitle to '{output_path}'")
    return output_path
