import requests
from pathlib import Path


def download_file(url, destination: Path):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raises an error if download failed

    # Ensure parent folder exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Write the content in chunks (good practice for large files)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # Filter out keep-alive chunks
                f.write(chunk)
    print(f"Downloaded to {destination}")
