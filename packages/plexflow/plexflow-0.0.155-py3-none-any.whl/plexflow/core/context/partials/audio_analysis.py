from plexflow.core.context.partial_context import PartialContext

class AudioAnalysis(PartialContext):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    def add_detected_languages(self, languages: set):
        self.set("audio/detected_languages", languages)
    
    def get_detected_languages(self) -> set:
        try:
            return self.get("audio/detected_languages")
        except:
            return set()
