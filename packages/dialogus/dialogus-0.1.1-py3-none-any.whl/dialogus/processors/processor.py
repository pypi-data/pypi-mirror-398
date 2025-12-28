import asyncio
import time
import types
from abc import abstractmethod
from typing import Coroutine, Generic, Optional, TypeVar, Union, get_args, get_origin

from loguru import logger

from dialogus.utils.base_object import BaseObject
from dialogus.messages.message import Message
from dialogus.observers.observer import (
    BaseObserver,
    MessageReceived,
    MessageProcessed,
    MessageError,
)
from dialogus.asynchronous.manager import TaskManager


MessageIn = TypeVar("MessageIn", bound=Message)
MessageOut = TypeVar("MessageOut", bound=Message)


class Processor(BaseObject, Generic[MessageIn, MessageOut]):
    """
    Base class for standalone message processors.

    A processor is a unit that:
    - Processes messages via the process() method
    - Can create and manage async tasks
    - Notifies observers of processing events

    Processors are standalone and don't know about other processors.
    For inter-processor communication, use Composite.
    """

    def __init__(
        self,
        *,
        task_manager: Optional[TaskManager] = None,
        observers: Optional[list[BaseObserver]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._task_manager = task_manager
        self._observers = observers or []
        self._input_types, self._output_types = self._extract_types()

    @classmethod
    def _extract_types(cls) -> tuple[set[type[Message]], set[type[Message]]]:
        """Extract input and output message types from the generic parameters."""
        for base in getattr(cls, "__orig_bases__", ()):
            args = get_args(base)
            if len(args) >= 2:
                input_type, output_type = args[0], args[1]

                def unpack(t: type[Message]) -> set[type[Message]]:
                    if get_origin(t) in (Union, types.UnionType):
                        return set[type[Message]](get_args(t))
                    return {t}

                return unpack(input_type), unpack(output_type)

        raise ValueError(f"Input and output message types not found for {cls}")

    @property
    def task_manager(self) -> TaskManager:
        if not self._task_manager:
            raise ValueError(f"Task manager not set for {self}")
        return self._task_manager

    @property
    def observers(self) -> list[BaseObserver]:
        return self._observers

    @property
    def input_types(self) -> set[type[Message]]:
        return self._input_types

    @property
    def output_types(self) -> set[type[Message]]:
        return self._output_types

    async def cleanup(self):
        if self._task_manager:
            await self._task_manager.cleanup()

    def create_task(
        self, coroutine: Coroutine, name: Optional[str] = None
    ) -> asyncio.Task:
        if name:
            name = f"{self}::{name}"
        else:
            name = f"{self}::{coroutine.cr_code.co_name}"  # ty: ignore[unresolved-attribute]
        return self.task_manager.create_task(coroutine, name)

    async def cancel_task(self, task: asyncio.Task, timeout: Optional[float] = 1.0):
        await self.task_manager.cancel_task(task, timeout)

    async def process(self, message: MessageIn) -> MessageOut:
        """
        Process a message and return the result.

        This is the main entry point for message processing. It handles observer notifications.
        """

        self.create_task(
            self._notify_received(message=message, received_at=time.monotonic_ns()),
            name="notify_received",
        )

        try:
            result = await self._process(message)
        except Exception as e:
            self.create_task(
                self._notify_error(
                    message=message, exception=e, error_at=time.monotonic_ns()
                ),
                name="notify_error",
            )
            raise

        self.create_task(
            self._notify_processed(
                message=message, result=result, processed_at=time.monotonic_ns()
            ),
            name="notify_processed",
        )

        return result

    @abstractmethod
    async def _process(self, message: MessageIn) -> MessageOut:
        """
        Process a message and return the result.

        Subclasses must implement this to define their message processing logic.
        This method receives a message and should return:
        - A new/modified message
        - The same message passed through
        """

    async def _notify_received(self, message: Message, received_at: int) -> None:
        if not self._observers:
            return

        data = MessageReceived(
            source_processor=self,
            source_message=message,
            content=message.content,
            received_at=received_at,
        )

        for observer in self._observers:
            try:
                await observer.on_message_received(data)
            except Exception as e:
                logger.exception(f"Observer {observer} failed on_message_received: {e}")

    async def _notify_processed(
        self,
        message: Message,
        result: Message,
        processed_at: int,
    ) -> None:
        if not self._observers:
            return

        data = MessageProcessed(
            source_processor=self,
            source_message=message,
            processed_message=result,
            content=result.content,
            processed_at=processed_at,
        )

        for observer in self._observers:
            try:
                await observer.on_message_processed(data)
            except Exception as e:
                logger.exception(
                    f"Observer {observer} failed on_message_processed: {e}"
                )

    async def _notify_error(
        self, message: Message, exception: Exception, error_at: int
    ) -> None:
        if not self._observers:
            return

        data = MessageError(
            source_processor=self,
            source_message=message,
            exception=exception,
            content=str(exception),
            error_at=error_at,
        )

        for observer in self._observers:
            try:
                await observer.on_message_error(data)
            except Exception as e:
                logger.exception(f"Observer {observer} failed on_message_error: {e}")
