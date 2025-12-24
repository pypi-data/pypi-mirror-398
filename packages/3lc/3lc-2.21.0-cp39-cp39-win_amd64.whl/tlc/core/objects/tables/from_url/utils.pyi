from tlc.core.object import Object as Object
from tlc.core.objects.mutable_objects import Configuration as Configuration
from tlc.core.objects.tables.from_url.table_from_coco import TableFromCoco as TableFromCoco
from tlc.core.url import Url as Url

def resolve_coco_table_url(json_file: str, image_root: str | None, dataset_name: str, project_name: str | None = None) -> Url:
    """Resolves a unique table url from the given parameters.

    If a table already exists matching the given parameters, the existing table url
    is returned. Otherwise, a new table url with a unique name is returned.
    """
def get_hash(paths: list[str], dataset_name: str) -> str: ...
def resolve_table_url(paths: list[str], dataset_name: str, project_name: str | None = None, prefix: str | None = None) -> Url:
    """Resolves a unique table url from the given parameters."""
def get_cache_file_name(table_url: Url) -> Url:
    """Returns the name of the cache file for the given table url."""
