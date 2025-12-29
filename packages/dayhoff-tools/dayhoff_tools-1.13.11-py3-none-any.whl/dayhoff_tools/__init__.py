import importlib.metadata

try:
    # The package name here should match the 'name' field in your pyproject.toml
    __version__ = importlib.metadata.version("dayhoff-tools")
except importlib.metadata.PackageNotFoundError:
    # This is a fallback for when the package might not be installed (e.g., running from source
    # without installation, or during development). You can set it to None, "unknown",
    # or handle it as you see fit.
    __version__ = "unknown"
