from pydantic import BaseModel


class PaginatorBase(BaseModel):  # pragma: no cover
    limit: int | None = None


class NumberPaginator(PaginatorBase):  # pragma: no cover
    offset: int | None = None


class CursorPaginator(PaginatorBase):  # pragma: no cover
    cursor: str | None = None
