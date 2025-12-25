import time

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr

from amsdal_utils.classes.transaction_manager import TransactionInfoManager
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.utils.lazy_object import LazyInstanceObject


class Transaction(BaseModel):
    r"""
    Represents a transaction in the system.

    Attributes:
        address (Address): The address of the transaction.
        label (str): The label of the transaction. Can be a name of transaction or a function name.
        tags (list\[str\]): The tags of the transaction. Can be used to group transactions.
        started_at (float): The timestamp when the transaction was started.
        ended_at (float): The timestamp when the transaction was ended.
    """

    _changes: LazyInstanceObject['Transaction', list[Reference]] = PrivateAttr(
        LazyInstanceObject(lambda transaction: TransactionInfoManager().get_changes(transaction))
    )
    address: Address
    label: str
    tags: list[str] = Field(default_factory=list)
    started_at: float = Field(default_factory=lambda: round(time.time() * 1000))
    ended_at: float = Field(default_factory=lambda: round(time.time() * 1000))

    @property
    def changes(self) -> list[Reference]:
        """
        Gets the list of References that the given transaction has created.

        Returns:
            list[Reference]: The list of References that the given transaction has created.
        """
        return self._changes.value(self)
