import requests
from typing import Union
from pathlib import Path
import socket
from requests.exceptions import RequestException
from importlib.resources import files


def get_jupyter_cell_script(filename: str) -> str:
    template_path = files("jupygrader.resources.jupyter_cell_scripts").joinpath(
        filename
    )

    return template_path.read_text()


def is_url(path: Union[str, Path]) -> bool:
    """Check if the path starts with http or https."""
    return str(path).lower().startswith(("http://", "https://"))


def download_file(url: str, destination: Path, timeout=30, max_retries=2) -> bool:
    """Download a file from a URL to a specified destination path.

    Args:
        url: The URL to download from
        destination: Path where the downloaded file should be saved
        verify_ssl: Whether to verify SSL certificates (default: True)
        timeout: Connection timeout in seconds (default: 30)
        max_retries: Number of retry attempts (default: 2)

    Returns:
        bool: True if download was successful, False otherwise
    """
    # Ensure parent folder exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries + 1):
        try:
            # Create a session for potential retries
            session = requests.Session()

            # Configure the request with timeout and SSL verification options
            response = session.get(
                url,
                stream=True,
                timeout=timeout,
            )

            # Raise an error if download failed for HTTP-level errors
            response.raise_for_status()

            # Write the content in chunks (good practice for large files)
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)

            return True

        except (socket.gaierror, socket.timeout) as e:
            # Handle DNS resolution failures and connection timeouts
            if attempt < max_retries:
                print(f"Connection error: {e}. Retry {attempt + 1}/{max_retries}...")
                continue

            print(
                f"Failed to resolve or connect to {url} when trying to copy to {destination}: {e}"
            )
            return False

        except RequestException as e:
            # Handle other request-related errors (HTTP errors, SSL errors, etc.)
            print(f"Failed when downloading from {url} to {destination}: {e}")
            return False

        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error downloading{url} to {destination}: {e}")
            return False
