import os
from groq import Groq
from pathlib import Path
from groq import Groq

# def transcribe_audio(file_path, model: str = 'medium'):
#     """
#     Transcribes an audio file using the Whisper model.

#     Args:
#         file_path (str): The path to the audio file to transcribe.

#     Returns:
#         str: The transcription of the audio file.

#     Raises:
#         FileNotFoundError: If the audio file does not exist.
#         Exception: If there is an error loading the model or transcribing the audio.

#     Example:
#         >>> transcribe_audio('path/to/your/audio/file.mp3')
#         'This is the transcribed text from your audio file.'

#     Note:
#         This function assumes that you have the Whisper model available locally.
#     """
#     try:
#         # Check if the file exists
#         with open(file_path, 'rb') as f:
#             pass
#     except FileNotFoundError as e:
#         raise e

#     try:
#         # Load the Whisper model
#         model = whisper.load_model(model)

#         # Transcribe the audio
#         result = model.transcribe(file_path)

#         return result["text"]
#     except Exception as e:
#         raise e

def transcribe_audio_groq(file_path: Path, model: str = 'distil-whisper-large-v3-en', prompt: str = None, **kwargs):
    """
    Transcribes an audio file using the Groq model.

    Args:
        file_path (Path): The path to the audio file to transcribe.
        model (str): The model to use for transcription.

    Returns:
        str: The transcription of the audio file.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        Exception: If there is an error with the Groq client or transcribing the audio.

    Example:
        >>> transcribe_audio_groq(Path('path/to/your/audio/file.m4a'))
        'This is the transcribed text from your audio file.'

    Note:
        This function assumes that you have the Groq client properly configured.
    """
    try:
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        # Check if the file exists
        if not file_path.exists():
            raise FileNotFoundError(f"No such file: '{file_path}'")

        print("GROQ_API_KEY:", os.environ.get("GROQ_API_KEY"))

        # Initialize the Groq client
        client = Groq()

        # Open the audio file
        with file_path.open("rb") as file:
            # Create a transcription of the audio file
            transcription = client.audio.transcriptions.create(
                file=(str(file_path), file.read()),  # Required audio file
                model=model,  # Required model to use for transcription
                prompt=prompt,  # Optional
                response_format=kwargs.get("response_format", "json"),  # Optional
                # language=kwargs.get("language", "en"),  # Optional
                temperature=0.0  # Optional
            )
            return transcription
    except Exception as e:
        raise e


def groq_inference(audio, **kwargs) -> dict:
    client = Groq()

    with open(audio, "rb") as file:
        transcription = client.audio.transcriptions.create(
        file=(audio, file.read()),
        model="whisper-large-v3",
    #      prompt="Kingdom of the Planet of the Apes: Many years after the reign of Caesar, a young ape goes on a journey that will lead him to question everything he's been taught $
        response_format="verbose_json",  # Optional
        language="en",  # Optional
        temperature=1.0,  # Optional
        timestamp_granularities=["word"],  # Optional
        )
        return transcription
    