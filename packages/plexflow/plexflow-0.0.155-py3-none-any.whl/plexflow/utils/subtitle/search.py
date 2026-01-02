import re

class SubtitleSearcher:
    """
    A class used to search for subtitles in a text.

    ...

    Attributes
    ----------
    hint_words : set
        a set of words to be used as hints in the subtitle search

    Methods
    -------
    compile_subtitle_hint_pattern(hint_word):
        Returns a compiled regular expression pattern based on the provided hint word.
    search_subtitles(text):
        Searches for subtitles in the provided text and returns a list of matches.
    """

    def __init__(self, hint_words):
        """
        Constructs all the necessary attributes for the SubtitleSearcher object.

        Parameters
        ----------
            hint_words : set
                a set of words to be used as hints in the subtitle search
        """
        self.hint_words = hint_words

    def compile_subtitle_hint_pattern(self, hint_word):
        """
        Returns a compiled regular expression pattern based on the provided hint word.

        The pattern searches for the hint word preceded by 'text' or 'subtitles' and 
        followed by any characters. The search is case-insensitive and includes newline 
        characters.

        Parameters
        ----------
            hint_word : str
                a word to be used as a hint in the subtitle search

        Returns
        -------
            pattern : re.Pattern
                a compiled regular expression pattern
        """
        pattern = re.compile(rf'\b(text|subs|subtitles?)\b(.*?)\b({hint_word})\.?\b', re.IGNORECASE | re.DOTALL | re.UNICODE)
        return pattern

    def search_subtitles(self, text):
        """
        Searches for subtitles in the provided text and returns a list of matches.

        The search is performed using the hint words provided during the object 
        initialization. Each hint word is used to compile a regular expression pattern, 
        which is then used to search the text.

        Parameters
        ----------
            text : str
                the text to be searched

        Returns
        -------
            matches : list
                a list of matches found in the text
        """
        matches = []
        for hint_word in self.hint_words:
            pattern = self.compile_subtitle_hint_pattern(hint_word)
            matches.extend([m.group(3) for m in re.finditer(pattern, text)])

        return ",".join(set([m.strip().lower() for m in matches]))
