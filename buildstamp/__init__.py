from buildstamp._metadata import BuildMetadata, load_metadata

try:
    _meta = load_metadata(__file__)
    __version__ = _meta.version
except FileNotFoundError:
    # No .git and no _version.json — we're being imported during a build step.
    _meta = None
    __version__ = "unknown"

__all__ = ["BuildMetadata", "load_metadata", "__version__"]
