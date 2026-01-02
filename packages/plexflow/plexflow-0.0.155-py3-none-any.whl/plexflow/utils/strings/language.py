
_language_mapping = {
    "dutch": "nl",
    "dut": "nl",
    "eng": "en",
    "english": "en",
    "nld": "nl",
    "ned": "nl",
    "nl": "nl",
    "en": "en",
}

def get_language_code(language: str) -> str:
    return _language_mapping.get(language.lower(), "unk")
