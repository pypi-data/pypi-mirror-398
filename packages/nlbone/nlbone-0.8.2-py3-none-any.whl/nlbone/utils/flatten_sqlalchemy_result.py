from typing import List, Any
from sqlalchemy import Row


def flatten_sqlalchemy_result(items: List[Any]) -> List[Any]:
    """
    Converts a list of SQLAlchemy Rows (tuples) into a flat list of entities
    with extra fields injected as attributes.
    """
    if not items:
        return []

    if not isinstance(items[0], Row):
        return items

    normalized = []
    for row in items:
        entity = row[0]

        for key, value in row._mapping.items():
            if not isinstance(value, type(entity)):
                setattr(entity, key, value)

        normalized.append(entity)

    return normalized
