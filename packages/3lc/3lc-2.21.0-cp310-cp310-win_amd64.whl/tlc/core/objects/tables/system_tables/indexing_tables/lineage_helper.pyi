from _typeshed import Incomplete
from tlc.core.object_registry import ObjectRegistry as ObjectRegistry
from tlc.core.objects.tables.system_tables.indexing_tables.table_indexing_table import TableIndexingTable as TableIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.table_info import TableInfo as TableInfo
from tlc.core.url import Scheme as Scheme, Url as Url

logger: Incomplete

def latest_revision_descending_from_url(url: Url, wait_for_rescan: bool, timeout: float | None) -> Url | None:
    '''Find the latest revision Url that descends from the provided Url by investigating the set of indexed Tables.

    This function uses the `create_graph` and `find_leaf_descendants_of` functions to build a graph of Table-revisions,
    identify leaf nodes that descend from the provided Url, and return the most recent revision.

    Sometimes it is not necessary to wait for a rescan of the indexed tables, but if the TableIndexingTable is known to
    be out of date, it can be re-scanned by setting the wait_for_rescan parameter to True together with a suitable
    timeout.

    :Example:

    ```python
    original_url = Url("http://example.com/parent-table.json")
    latest_revision_url = latest_revision_descending_from_url(original_url)
    ```

    Note that if the requested Url is not present in the TableIndexingTable, a ValueError is raised. This typically
    indicates that the Url has not been persisted yet or is not a part of the current indexed set.

    :param url: The original Url from which to trace the latest revision.
    :param wait_for_rescan: If True, the TableIndexingTable will re-scan for updates. If False, the TableIndexingTable
                   will be used as-is and may be out of date. Note that Tables created in this thread will automatically
                   appear in the TableIndexingTable without the need to scan.
    :param timeout: The maximum time to wait for the TableIndexingTable to be updated, in seconds. None means block
        until completion.

    :returns: A Url of the latest revision that descends from the original Url. If there is no revision that descends
              from the provided Url, None is returned.
    '''
def create_forward_graph(revisions: list[TableInfo]) -> dict[str, set[str]]:
    """Creates a forward graph from a list of table revisions.

    This function takes a list of table revisions and constructs a directed graph where nodes are revision Urls and
    edges represent the lineage from one revision to another.
    This differs from the representation in TableInfo but makes searching for children easier.

    If a revision has input_urls that are not present in the revisions-list, it means that the Table/Url pointed to is
    not (yet) indexed, this is a valid case and such links are ignored, ie. the graph only represents the part of the
    revision tree that is indexed.

    This method also checks for cycles in the graph and raises a ValueError if any are found.
    """
def find_leaf_descendants_of(graph: dict[str, set[str]], start_url: str) -> set[str]:
    """Find all leaf nodes in the graph that descend from a given starting Url.

    This function performs a depth-first search on the provided graph, starting from the start_url. It collects all
    leaf nodes encountered during the search.

    :Example:

    ```python
    graph = create_graph(revisions)
    leaf_nodes = find_leaf_descendants_of(graph, start_url)
    ```

    :param graph: The graph to search, represented as a dictionary.
    :param start_url: The starting Url for the search.

    :returns: A set of Urls that are leaf nodes descending from the starting Url.
    :raises: ValueError: If the start_url is not present in the graph.
    """
