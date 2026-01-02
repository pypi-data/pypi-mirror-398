
import json
import os
import cohere
from plexflow.core.genai.utils.loader import load_preamble

class Plexa:
    def __init__(self) -> None:
        self.bot_name = "Plexa"
        self.co = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
        self.chat_history = []
        self.preamble = load_preamble("plexa_v2")
        self.hint = "BE BRIEF IN YOUR RESPONSE, SPLIT TEXT IN MESSAGES AND FORMAT AS VALID JSON"
    
    def add_user_message(self, message: str, context: dict):
        self.chat_history.append({
            "role": "USER", "text":
                json.dumps({
                    "movie": context.get("title"),
                    "release_date": context.get("release_date"),
                    "user_question": message,
                    "hint": self.hint,
                })
            })
    
    def add_bot_message(self, message: str, context: dict):
        self.chat_history.append({
            "role": "CHATBOT", "text":
                json.dumps({
                    "response": message,
                    "parts": [
                        message
                    ]
                })
            })

    def react(self, question: str, context: dict):
        message = json.dumps({
            "movie": context.get("title"),
            "release_date": context.get("release_date"),
            "user_question": question,
            "hint": self.hint,
        })

        return self.co.chat(
                    message=message,
                    temperature=1,
                    connectors=[{"id": "web-search"}],
                    model="command-r-plus",
                    chat_history=self.chat_history[-10:],
                    preamble=self.preamble,
                )
    
    