from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from amsdal_utils.errors import AmsdalInitiationError
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.utils.singleton import Singleton

if TYPE_CHECKING:
    from amsdal_utils.models.data_models.transaction import Transaction


class TransactionInfoQueryBase(ABC):
    @classmethod
    @abstractmethod
    def get_changes(cls, transaction: 'Transaction') -> list['Reference']:
        """
        Get the list of References that the given transaction has created.

        Args:
            transaction (Transaction): The transaction.

        Returns:
            list[Reference]: The list of References that the given transaction has created.
        """


class TransactionInfoManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._transaction_info_query: type[TransactionInfoQueryBase] | None = None

    def register_transaction_info_query(self, transaction_info_query: type[TransactionInfoQueryBase]) -> None:
        """
        Registers a transaction info query class.

        Args:
            transaction_info_query (type[TransactionInfoQueryBase]): The transaction info query class.

        Returns:
            None
        """
        self._transaction_info_query = transaction_info_query

    def get_transaction_info_query(self) -> type[TransactionInfoQueryBase]:
        """
        Gets the registered transaction info query class.

        Returns:
            type[TransactionInfoQueryBase]: The registered transaction info query class.

        Raises:
            AmsdalInitiationError: If no transaction info query class is registered.
        """
        if self._transaction_info_query is None:
            msg = 'TransactionInfoQuery is not registered.'
            raise AmsdalInitiationError(msg)

        return self._transaction_info_query

    def get_changes(self, transaction: 'Transaction') -> list['Reference']:
        """
        Gets the list of References that the given transaction has created.

        Args:
            transaction (Transaction): The transaction.

        Returns:
            list[Reference]: The list of References that the given transaction has created.
        """
        return self.get_transaction_info_query().get_changes(transaction)
