import uuid


def get_identifier() -> str:  # pragma: no cover
    return uuid.uuid4().hex
