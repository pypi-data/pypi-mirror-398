from functools import lru_cache

import yaml

from .._types.catalog import Catalog


@lru_cache(maxsize=None)
def load_catalog_file(file_path: str) -> Catalog:
    """
    Load catalog from YAML file with caching.

    This function caches the loaded catalog to avoid repeated file I/O.
    The cache is cleared when clear_cache() is called.

    Args:
        file_path: Path to YAML file containing translation catalog.

    Returns:
        Translation catalog loaded from file.
    """
    with open(file_path, encoding="utf-8") as f:
        catalog: Catalog = yaml.safe_load(f)
        return catalog
