
from pathlib import Path

import requests_cache
from loguru import logger as log
from platformdirs import user_cache_path

CACHE_DIR = Path(user_cache_path("ptr-editor"))
CACHE_EXPIRE_AFTER = 3600  # seconds (1 hour)

# Base URL for remote data files
BASE_URL = "https://juicept.esac.esa.int/assets/DATA"

# Registry of available remote files
REMOTE_FILES = {
    "snippets": {
        "url": f"{BASE_URL}/snippets/snippets.txt",
        "filename": "snippets.txt",
    },
    # Add more files here as needed:
    # "config": {
    #     "url": f"{BASE_URL}/config/config.json",
    #     "filename": "config.json",
    # },
}

# Create a cached session for HTTP requests
_session = requests_cache.CachedSession(
    cache_name=str(CACHE_DIR / "http_cache"),
    backend="sqlite",
    expire_after=CACHE_EXPIRE_AFTER,
    allowable_codes=(200,),
    stale_if_error=True,  # Use stale cache if download fails
)


def get_remote_file(file_key: str, timeout: float = 5.0) -> str:
    """
    Get a remote file path, downloading and caching with automatic revalidation.

    Uses requests-cache to handle HTTP caching headers (ETags, Last-Modified)
    and only downloads if the file has changed on the server.

    Falls back to cached version, then to bundled file if download fails.

    Args:
        file_key: Key identifying the file in REMOTE_FILES registry.
        timeout: Request timeout in seconds (default: 5.0).

    Returns:
        str: Path to the local file.

    Raises:
        KeyError: If file_key is not found in REMOTE_FILES registry.
        FileNotFoundError: If download fails, no cache exists, and no bundled file found.
    """
    if file_key not in REMOTE_FILES:
        msg = f"Unknown file key: {file_key}. Available: {list(REMOTE_FILES.keys())}"
        log.error(msg)
        raise KeyError(msg)

    file_info = REMOTE_FILES[file_key]
    url = file_info["url"]
    filename = file_info["filename"]

    log.debug(f"Retrieving file '{file_key}' (filename: {filename})")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = CACHE_DIR / filename

    try:
        log.debug(f"Attempting to download from {url} (timeout: {timeout}s)")
        response = _session.get(url, timeout=timeout)
        response.raise_for_status()

        # Check if response came from cache
        if hasattr(response, "from_cache") and response.from_cache:
            log.debug(f"File '{file_key}' retrieved from HTTP cache")
        else:
            log.info(f"Downloaded '{file_key}' from {url}")

        local_path.write_bytes(response.content)
        log.debug(f"Saved '{file_key}' to {local_path}")
        return str(local_path)

    except Exception as e:
        log.warning(f"Failed to download '{file_key}': {e}")

        # Try cached version first
        if local_path.exists():
            log.info(f"Using cached version of '{file_key}' at {local_path}")
            return str(local_path)

        # Fallback to bundled file
        bundled_path = Path(__file__).parent / filename
        if bundled_path.exists():
            log.info(f"Using bundled version of '{file_key}' at {bundled_path}")
            return str(bundled_path)

        msg = f"Could not download {file_key} and no local fallback available"
        log.error(msg)
        raise FileNotFoundError(msg) from None


def get_snippet_file() -> str:
    """
    Get the snippet file path (convenience wrapper).

    Returns:
        str: Path to the local snippet file.

    Raises:
        FileNotFoundError: If file cannot be retrieved.
    """
    return get_remote_file("snippets")


def invalidate_cache(file_key: str | None = None) -> None:
    """
    Invalidate the cache and force redownload on next request.

    Args:
        file_key: Specific file to invalidate, or None to clear all caches.

    Examples:
        >>> invalidate_cache("snippets")  # Clear only snippets cache
        >>> invalidate_cache()  # Clear all caches
    """
    if file_key is None:
        # Clear all HTTP cache and local files
        _session.cache.clear()
        log.info("Cleared all HTTP cache")
        for file_info in REMOTE_FILES.values():
            local_path = CACHE_DIR / file_info["filename"]
            if local_path.exists():
                local_path.unlink()
                log.debug(f"Deleted cached file: {local_path}")
    else:
        # Clear specific file
        if file_key not in REMOTE_FILES:
            available = list(REMOTE_FILES.keys())
            msg = f"Unknown file key: {file_key}. Available: {available}"
            raise KeyError(msg)

        file_info = REMOTE_FILES[file_key]
        url = file_info["url"]
        filename = file_info["filename"]

        # Delete from HTTP cache
        _session.cache.delete(urls=[url])
        log.debug(f"Deleted {url} from HTTP cache")

        # Delete local file
        local_path = CACHE_DIR / filename
        if local_path.exists():
            local_path.unlink()
            log.debug(f"Deleted cached file: {local_path}")
