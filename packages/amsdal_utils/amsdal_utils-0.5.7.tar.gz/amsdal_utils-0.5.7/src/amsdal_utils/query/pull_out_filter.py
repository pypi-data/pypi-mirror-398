from typing import Any

from amsdal_utils.query.utils import ConnectorEnum
from amsdal_utils.query.utils import Q


def pull_out_filter_from_query(query: Q, filter_name: str) -> tuple[set[Any], Q | None]:
    """
    Extracts a specific filter from a query and returns the remaining query.

    Args:
        query (Q): The query object to process.
        filter_name (str): The name of the filter to extract.

    Returns:
        tuple[set[Any], Q | None]: A tuple containing the set of pulled values and the modified query.
    """
    if query.connector != ConnectorEnum.AND:
        msg = 'Only AND connector is supported'
        raise ValueError(msg)

    pulled_values = set()
    result_query = query.__copy__()
    result_query.children = []

    for child in query.children:
        if isinstance(child, Q):
            _values, _q = pull_out_filter_from_query(child, filter_name)
            pulled_values.update(_values)

            if _q is not None:
                result_query.children.append(_q)

            continue

        if child.field_name == filter_name:
            pulled_values.add(child.value)
        else:
            result_query.children.append(child)

    if result_query.children:
        if len(result_query.children) == 1 and isinstance(result_query.children[0], Q):
            return pulled_values, result_query.children[0]
        else:
            return pulled_values, result_query

    return pulled_values, None
