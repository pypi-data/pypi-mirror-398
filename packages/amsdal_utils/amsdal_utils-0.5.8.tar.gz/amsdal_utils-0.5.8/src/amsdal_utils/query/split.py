from amsdal_utils.query.data_models.filter import Filter
from amsdal_utils.query.utils import ConnectorEnum
from amsdal_utils.query.utils import Q


def split_q(query: Q | Filter) -> list[Q]:
    """
    Splits a Q object into a list of Q objects by OR.

    Args:
        query (Q | Filter): The query object to split.

    Returns:
        list[Q]: A list of Q objects split by OR.
    """
    if isinstance(query, Filter):
        return [Q(query)]

    if len(query.children) == 1:
        return [query]

    if query.connector == ConnectorEnum.OR:
        if query.negated:
            return _process_and_split(_reverse_q(query))

        return _process_or_split(query)

    if query.negated:
        return _process_or_split(_reverse_q(query))

    return _process_and_split(query)


def _process_and_split(query: Q) -> list[Q]:
    splits: list[Q] = []

    for child_q in query.children:
        child_splits = split_q(child_q)

        if not splits:
            splits = child_splits
            continue

        new_splits = []

        for existing_split in splits:
            for child_split in child_splits:
                new_splits.append(existing_split & child_split)

        splits = new_splits

    return splits


def _process_or_split(query: Q) -> list[Q]:
    splits = []

    for child_q in query.children:
        splits.extend(split_q(child_q))

    return splits


def _reverse_q(query: Q) -> Q:
    return Q(
        *[~child_q if isinstance(child_q, Q) else ~Q(child_q) for child_q in query.children],
        negated=not query.negated,
        connector=ConnectorEnum.OR if query.connector == ConnectorEnum.AND else ConnectorEnum.AND,
    )
