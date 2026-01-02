from plexflow.utils.transcribe.speech2text import transcribe_audio
import os
from typing import Any, Dict

def get_captcha_code_from_audio(file_path: str, **kwargs: Dict[str, Any]) -> str:
    """
    Transcribes an audio file to text, representing a CAPTCHA code.

    This function takes the path of an audio file as input, transcribes it to text using the `transcribe_audio` function,
    and returns the transcribed text as a CAPTCHA code. The returned CAPTCHA code has no whitespace, is in all caps,
    and contains no punctuation.

    Args:
        file_path (str): The path of the audio file to transcribe.
        **kwargs: Arbitrary keyword arguments for the `transcribe_audio` function.

    Returns:
        str: The transcribed CAPTCHA code.

    Raises:
        RuntimeError: If the transcription fails for any reason.
    """
    try:
        # Transcribe the audio file to text
        text = transcribe_audio(file_path=file_path, **kwargs)
        
        # Remove whitespace, convert to uppercase, and remove punctuation
        captcha_code = ''.join(char for char in text if char.isalnum()).upper()

        return captcha_code

    except Exception as e:
        error_message = f"Failed to get CAPTCHA code from audio file: {os.path.abspath(file_path)}"
        raise RuntimeError(error_message) from e
