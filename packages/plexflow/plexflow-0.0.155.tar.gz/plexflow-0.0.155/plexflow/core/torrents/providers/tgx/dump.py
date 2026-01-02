import pandas as pd
import re
from typing import Optional
from plexflow.utils.download.gz import download_and_extract_gz

ID_PATTERN = re.compile(r'/torrent/(\d+)/', re.IGNORECASE)

def extract_id(url: str) -> Optional[str]:
    """
    Extracts the ID from the given URL using a regular expression.

    Args:
        url (str): The URL from which to extract the ID.

    Returns:
        str: The extracted ID if found, otherwise None.
    """
    match = ID_PATTERN.search(url)
    return match.group(1) if match else None

def read_and_transform_dump(url: str, output_filename: str) -> pd.DataFrame:
    """
    Downloads, extracts, and transforms a gzipped dump file into a DataFrame.

    This function downloads a gzipped dump file from the specified URL, extracts it, 
    and reads the data into a DataFrame. It then renames the columns and adds a new 
    column 'id' by extracting the ID from the 'url' column.

    Args:
        url (str): The URL of the gzipped dump file to download.
        output_filename (str): The filename for the extracted file.

    Returns:
        pd.DataFrame: The transformed DataFrame.
    """
    download_and_extract_gz(url, output_filename)

    df = pd.read_csv(output_filename, sep='|', header=None, names=["hash", "name", "category", "url", "torrent"])
    df["id"] = df.url.apply(extract_id)
    return df
