import string
import re

def remove_punctuation(text):
  """Removes all punctuation from a given string."""
  if not isinstance(text, str):
    return "" # Handle non-string input gracefully

  translator = str.maketrans('', '', string.punctuation)
  return text.translate(translator)

def clean_string(input_string, remove_spaces: bool = False, remove_years: bool = False):
    """
    Strips all punctuation, spaces, and optionally years from a string and converts it to lowercase.

    Args:
        input_string (str): The string to clean.
        remove_spaces (bool): If True, all spaces are removed. Defaults to False.
        remove_years (bool): If True, all 4-digit numbers are removed. Defaults to False.

    Returns:
        str: The cleaned string.
    """
    # Create a translation table to remove punctuation
    translator = str.maketrans('', '', string.punctuation)

    # Remove punctuation using the translation table
    no_punctuation = input_string.translate(translator)

    # Remove all 4-digit numbers if requested
    if remove_years:
        no_punctuation = re.sub(r'\b\d{4}\b', '', no_punctuation)

    # Remove all spaces if requested
    no_spaces = no_punctuation.replace(" ", "") if remove_spaces else no_punctuation

    # Convert to lowercase
    cleaned_string = no_spaces.lower()

    return cleaned_string.strip()
