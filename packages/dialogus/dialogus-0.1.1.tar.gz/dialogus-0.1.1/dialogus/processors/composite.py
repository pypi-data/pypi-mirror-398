import asyncio
from typing import Optional, Sequence

from loguru import logger

from dialogus.messages.message import EgressMessage, Message
from dialogus.processors.processor import Processor
from dialogus.processors.topology import Topology
from dialogus.utils.exceptions import MaxHopsExceededError


class Composite(Processor[Message, Message]):
    def __init__(
        self,
        *,
        processors: Sequence[Processor],
        max_hops: int = 30,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._topology = Topology(processors)
        self._max_hops = max_hops
        self._current_task: Optional[asyncio.Task] = None
        self.setup_task_managers()

    async def interrupt_processor(self):
        if self._current_task:
            await self.cancel_task(self._current_task, timeout=1.0)

    def setup_task_managers(self):
        for processor in self._topology.processors:
            if not processor._task_manager:
                processor._task_manager = self._task_manager

    async def _process(
        self,
        message: Message,
        hops: int = 0,
    ) -> Message:
        while hops < self._max_hops:
            processor = self._topology.mapping[type(message)]

            # Process message with cancellation support
            try:
                task = self.create_task(
                    processor.process(message), name=f"process::{processor.name}"
                )
                self._current_task = task
                result = await task
            except asyncio.CancelledError:
                logger.warning(f"Processing of {message} was interrupted.")
                break
            finally:
                self._current_task = None

            # Terminal conditions
            if issubclass(type(result), EgressMessage):
                return result

            # Continue chain with result
            message = result
            hops += 1

        raise MaxHopsExceededError(
            f"Max hops ({self._max_hops}) exceeded while processing {message}."
        )
