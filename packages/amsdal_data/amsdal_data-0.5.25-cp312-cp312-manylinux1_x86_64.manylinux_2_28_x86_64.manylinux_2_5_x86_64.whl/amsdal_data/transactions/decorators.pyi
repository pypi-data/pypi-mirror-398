from _typeshed import Incomplete
from amsdal_data.data_models.transaction_context import TransactionContext as TransactionContext
from amsdal_data.enums import CoreResource as CoreResource
from amsdal_data.transactions.background.manager import AsyncBackgroundTransactionManager as AsyncBackgroundTransactionManager, BackgroundTransactionManager as BackgroundTransactionManager
from amsdal_data.transactions.background.schedule.config import SCHEDULE_TYPE as SCHEDULE_TYPE, ScheduleConfig as ScheduleConfig
from amsdal_data.transactions.constants import TRANSACTION_CLASS_NAME as TRANSACTION_CLASS_NAME
from collections.abc import Callable as Callable, Coroutine
from typing import Any, ParamSpec, Protocol, TypeVar, overload

P = ParamSpec('P')
R = TypeVar('R')
R_co = TypeVar('R_co', covariant=True)

class Transaction(Protocol[P, R_co]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...
    def submit(self, *args: P.args, **kwargs: P.kwargs) -> None: ...

class AsyncTransaction(Protocol[P, R_co]):
    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...
    def submit(self, *args: P.args, **kwargs: P.kwargs) -> None: ...

@overload
def transaction(name: Callable[P, R]) -> Transaction[P, R]: ...
@overload
def transaction(name: str | None = None, schedule_config: ScheduleConfig | None = None, schedule: SCHEDULE_TYPE | None = None, **transaction_kwargs: Any) -> Callable[[Callable[P, R]], Transaction[P, R]]: ...
@overload
def async_transaction(name: Callable[P, Coroutine[Any, Any, R]]) -> AsyncTransaction[P, R]: ...
@overload
def async_transaction(name: str | None = None, schedule_config: ScheduleConfig | None = None, schedule: SCHEDULE_TYPE | None = None, **transaction_kwargs: Any) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], AsyncTransaction[P, R]]: ...
def raw_transaction(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to execute a function within a transaction flow context.

    This decorator wraps the provided function, ensuring it is executed within a transaction flow.
    It captures the return value and handles any exceptions that may occur during execution.

    Args:
        func (Callable[P, R]): The function to be executed within the transaction flow.

    Returns:
        Callable[P, R]: The wrapped function that executes within a transaction flow.
    """

class TransactionFlow:
    return_value: Any
    context: Incomplete
    transaction_kwargs: dict[str, Any]
    def __init__(self, func: Callable[..., Any], *args: Any, transaction_kwargs: dict[str, Any], **kwargs: Any) -> None: ...
    def __enter__(self) -> TransactionFlow: ...
    async def __aenter__(self) -> TransactionFlow: ...
    def set_return_value(self, value: Any) -> None: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    def _serialize_arguments(self, data: Any) -> Any: ...
    @staticmethod
    def _get_execution_location(func: Any) -> str: ...
