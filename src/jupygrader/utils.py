import requests
from typing import Union
from pathlib import Path
from requests.exceptions import ConnectionError, RequestException, Timeout
from importlib.resources import files
import click
from functools import wraps
import os
import glob


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
        timeout: Connection timeout in seconds (default: 30)
        max_retries: Number of retry attempts for connection errors and
            timeouts (default: 2)

    Returns:
        bool: True if download was successful, False otherwise
    """
    # Ensure parent folder exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
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

        except (ConnectionError, Timeout) as e:
            # Retry transient connection failures and timeouts
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
            print(f"Unexpected error downloading {url} to {destination}: {e}")
            return False

    return False


def process_notebook_paths(func):
    """
    A decorator that processes the `notebook_paths` argument.

    It takes the tuple of user-provided paths and glob patterns, resolves them
    into a flat list of existing .ipynb files, and replaces the original
    argument before calling the decorated command function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        resolved_paths = []
        # The 'notebook_paths' argument from click is passed in kwargs
        for path in kwargs["notebook_paths"]:
            if os.path.isfile(path) and path.endswith(".ipynb"):
                resolved_paths.append(os.path.abspath(path))
            elif os.path.isdir(path):
                pattern = os.path.join(os.path.abspath(path), "*.ipynb")
                found = glob.glob(pattern)
                if found:
                    click.echo(f"Found {len(found)} notebooks in directory: {path}")
                resolved_paths.extend(found)
            else:
                found = glob.glob(path, recursive=True)
                ipynb_files = [
                    os.path.abspath(f) for f in found if f.endswith(".ipynb")
                ]
                resolved_paths.extend(ipynb_files)

        if not resolved_paths:
            click.echo(
                "Error: No notebook files found matching the provided paths.", err=True
            )
            raise click.Abort()

        # Overwrite the original `notebook_paths` tuple with the new, sorted, unique list of files
        kwargs["notebook_paths"] = sorted(list(set(resolved_paths)))

        return func(*args, **kwargs)

    return wrapper
