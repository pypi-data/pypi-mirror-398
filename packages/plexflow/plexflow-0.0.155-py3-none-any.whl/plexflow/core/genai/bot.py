import os
import cohere
from plexflow.core.genai.utils.loader import load_preamble

class CohereBot:
    def __init__(self, preamble_id: str) -> None:
        self.co = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
        self.chat_history = []
        self.preamble = load_preamble(preamble_id)
