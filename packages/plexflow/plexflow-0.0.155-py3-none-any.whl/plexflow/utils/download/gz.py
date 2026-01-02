import requests
import gzip
import io

def download_and_extract_gz(url, output_filename):
    """Download and extract a .gz file from a URL.

    Parameters:
    url (str): The URL of the .gz file to download.
    output_filename (str): The name of the output file.

    Returns:
    None
    """
    # Download the file
    response = requests.get(url)
    compressed_file = io.BytesIO(response.content)

    # Decompress the file
    decompressed_file = gzip.GzipFile(fileobj=compressed_file)

    # Write to a .txt file
    with open(output_filename, "wb") as outfile:
        outfile.write(decompressed_file.read())

    print(f"File downloaded and extracted to {output_filename} successfully.")
