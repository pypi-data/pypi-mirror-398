import re
import bitmath
from humanfriendly import parse_size as parse_size_to_bytes

def parse_size(sentence):
    """
    Parses the sizes from a sentence and returns them in bytes.

    Args:
        sentence (str): The sentence containing sizes to be parsed.

    Returns:
        list: A list of sizes in bytes.

    """
    try:
        size = bitmath.parse_string(sentence)
        return [size.to_Byte().value]
    except ValueError:
        pass
    
    # Regular expression pattern for a size with optional space between number and unit
    pattern = r'\b\d+(?:\.\d+)?\s*[KkMmGgTtPpEeZzYy]?[i]?[Bb]?\b'
    
    # Find all sizes in the sentence
    matches = re.findall(pattern, sentence, re.IGNORECASE)
    
    sizes = []
    for match in matches:
        try:
            # Remove any spaces within the match to ensure bitmath can parse it
            size_str = match.replace(" ", "")
            
            try:
                # Parse the size to a bitmath object
                size = bitmath.parse_string(size_str)
                
                # Convert the size to bytes and return
                sizes.append(size.to_Byte().value)
            except Exception as e:
                print(e)
                size = parse_size_to_bytes(size_str)
                sizes.append(size)
    
        except ValueError as e:
            print(f"Error parsing size: {e}")
    
    return sizes


if __name__ == '__main__':
    # Test the parse_size function    
    sizes = parse_size('My size is 6.40 GB')
    
    print(sizes)