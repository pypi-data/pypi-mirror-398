from plexflow.core.genai.bot import CohereBot
import json

class MovieTorrentParser(CohereBot):
    def __init__(self) -> None:
        super().__init__(preamble_id="movie_torrent_parser")
    
    def parse(self, content: str):
        response = self.co.chat(
            message=content,
            temperature=1,
            model="command-r-plus",
            preamble=self.preamble,
        )
        
#        print(response.json())
        content = response.text
        
        if content.startswith('```json'):
            content = content.lstrip("`json")
        
        if content.endswith('`'):
            content = content.rstrip("`")

        return json.loads(content)