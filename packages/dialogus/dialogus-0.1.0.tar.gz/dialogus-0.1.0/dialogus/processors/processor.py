import asyncio
import time
from abc import abstractmethod
from typing import Coroutine, Optional

from loguru import logger

from dialogus.utils.base_object import BaseObject
from dialogus.messages.message import Message
from dialogus.observers.observer import (
    BaseObserver,
    MessageReceived,
    MessageProcessed,
)
from dialogus.asynchronous.manager import TaskManager


class Processor(BaseObject):
    """
    Base class for standalone message processors.

    A processor is a unit that:
    - Processes messages via the process() method
    - Can create and manage async tasks
    - Notifies observers of processing events
    - Handles errors gracefully

    Processors are standalone and don't know about other processors.
    For inter-processor communication, use Composite.
    """

    def __init__(
        self,
        *,
        task_manager: TaskManager,
        output_types: Optional[set[type[Message]]] = None,
        observers: Optional[list[BaseObserver]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._task_manager = task_manager
        self._observers = observers or []
        self._output_types = output_types

    @property
    def task_manager(self) -> TaskManager:
        return self._task_manager

    @property
    def observers(self) -> list[BaseObserver]:
        return self._observers

    @property
    def output_types(self) -> Optional[set[type[Message]]]:
        return self._output_types

    async def cleanup(self):
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

    async def process(self, message: Message) -> Message:
        """
        Process a message and return the result.

        This is the main entry point for message processing. It handles:
        - Observer notifications
        - Error handling
        - Routing from and to other processors
        """

        self.create_task(self._notify_received(message), name="notify_received")

        try:
            result = await self._process(message)
        except Exception as e:
            self.create_task(self._notify_error(message, e), name="notify_error")
            raise

        self.create_task(
            self._notify_processed(message, result),
            name="notify_processed",
        )

        return result

    @abstractmethod
    async def _process(self, message: Message) -> Message:
        """
        Process a message and return the result.

        Subclasses must implement this to define their message processing logic.
        This method receives a message and should return:
        - A new/modified message
        - The same message passed through
        """

    async def _notify_received(self, message: Message) -> None:
        if not self._observers:
            return

        data = MessageReceived(
            source_processor=self,
            source_message=message,
            content=message.content,
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
    ) -> None:
        if not self._observers:
            return

        data = MessageProcessed(
            source_processor=self,
            source_message=message,
            result_message=result,
            content=result.content,
        )

        for observer in self._observers:
            try:
                await observer.on_message_processed(data)
            except Exception as e:
                logger.exception(
                    f"Observer {observer} failed on_message_processed: {e}"
                )

    async def _notify_error(self, message: Message, exception: Exception) -> None:
        if not self._observers:
            return

        for observer in self._observers:
            try:
                await observer.on_message_error(message=message, exception=exception)
            except Exception as e:
                logger.exception(f"Observer {observer} failed on_message_error: {e}")
