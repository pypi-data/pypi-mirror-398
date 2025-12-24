program define jptools
    version 17.0
    // Parse syntax: both URL() and FILE() are required
    syntax , URL(string) FILE(string)

    // Check that Python is configured and ready
    capture python query
    if _rc {
        di as err "Python is not configured in Stata. Use {bf:set python_exec} to set it up."
        exit 198
    }

    // Call the Python helper function
    python: _jptools("`url'", "`file'")
end


python:
from jp_tools import download
import os

def _jptools(url: str, filename: str):
    """
    Downloads a file from a URL to a specified local path using jp_tools.download().
    """
    # Basic sanity checks
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url}. Must start with http:// or https://")

    # Create directories if needed
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

    try:
        print(f"Downloading from: {url}")
        download(url=url, filename=filename)
        print(f"File saved to: {os.path.abspath(filename)}")
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")
end


