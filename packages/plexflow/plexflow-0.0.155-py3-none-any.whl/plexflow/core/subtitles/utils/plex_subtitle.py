
class PlexSubtitle:
    def __init__(self, path: str, name: str):
        self.path = path
        self.name = name
        self.detected_language = None

    @property
    def filepath(self) -> str:
        return self.path

    @property
    def filename(self) -> str:
        return self.name
    
    def set_detected_language(self, lang):
        self.detected_language = lang
    
    @property
    def language(self) -> str:
        return self.detected_language