"""Version utilities shared across CLI components."""

from importlib import metadata as importlib_metadata


def get_installed_appserver_version() -> str | None:
    """Return the installed version of `llama-deploy-appserver`, if available."""
    try:
        return importlib_metadata.version("llama-deploy-appserver")
    except Exception:
        return None
