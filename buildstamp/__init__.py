from buildstamp._metadata import BuildMetadata, load_metadata

_meta = load_metadata(__file__)
__version__ = _meta.version

__all__ = ["BuildMetadata", "load_metadata", "__version__"]
