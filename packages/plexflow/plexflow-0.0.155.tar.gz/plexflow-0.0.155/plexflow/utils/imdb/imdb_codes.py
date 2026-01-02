import re

class IMDbCode:
    """A class to represent an IMDb code.

    Attributes:
        code (str): A string representing the IMDb code.

    Methods:
        __str__(): Returns the IMDb code as a string.
        __eq__(other): Compares the IMDb code with another IMDb code or string.
        normalize_code(code: str) -> str: Normalizes an IMDb code by removing the leading 'tt' and any leading zeros.
    """

    def __init__(self, code):
        """
        Constructs an IMDbCode instance with the provided IMDb code.

        Parameters
        ----------
        code : str
            a string representing the IMDb code

        Raises
        ------
        ValueError
            If `code` is not a string.
        """
        if not isinstance(code, str):
            raise ValueError("IMDb code must be a string.") from None

        self.code = code.lower()

    def __str__(self):
        """Returns the IMDb code as a string."""
        return self.code

    def __eq__(self, other):
        """
        Compares the IMDb code with another IMDb code or string.

        Parameters
        ----------
        other : IMDbCode or str
            the other IMDb code or string to compare with

        Returns
        -------
        bool
            True if the IMDb codes are equal, False otherwise

        Raises
        ------
        TypeError
            If `other` is not an IMDbCode or a string.
        """
        if isinstance(other, IMDbCode):
            return self.normalize_code(self.code) == self.normalize_code(other.code)
        elif isinstance(other, str):
            return self.normalize_code(self.code) == self.normalize_code(other)
        else:
            raise TypeError("Can only compare IMDbCode with another IMDbCode or a string.") from None

    @staticmethod
    def normalize_code(code):
        """
        Normalizes an IMDb code by removing the leading 'tt' and any leading zeros.

        Parameters
        ----------
        code : str
            the IMDb code to normalize

        Returns
        -------
        str
            the normalized IMDb code
        """
        # Remove leading 'tt' if present
        if code.startswith('tt'):
            code = code[2:]
        # Remove leading zeros
        code = code.lstrip('0')
        return code


def extract_imdb_code(s: str):
    """
    Generator function to extract all IMDB codes from a given string.

    IMDB codes are assumed to follow the format 'tt' followed by 7 or more digits.

    Args:
        s (str): The string to search for IMDB codes.

    Yields:
        str: The next IMDB code found in the string. If no code is found, the function simply returns.

    Examples:
        >>> list(extract_imdb_code('https://www.imdb.com/title/tt0111161/ and https://www.imdb.com/title/tt006864600/'))
        ['tt0111161', 'tt006864600']

        >>> list(extract_imdb_code('this string has no imdb code'))
        []
    """
    for match in re.finditer(r'tt\d{7,}', s):
        yield match.group(0)
