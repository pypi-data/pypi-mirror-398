from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dialogus.messages import Message

if TYPE_CHECKING:
    from dialogus.processors.processor import Processor


@dataclass(frozen=True)
class MessageReceived(Message):
    source_processor: "Processor"
    source_message: Message


@dataclass(frozen=True)
class MessageProcessed(Message):
    source_processor: "Processor"
    source_message: Message
    result_message: Message


class BaseObserver(ABC):
    @abstractmethod
    async def on_message_received(self, message: MessageReceived) -> None: ...

    @abstractmethod
    async def on_message_processed(self, message: MessageProcessed) -> None: ...

    @abstractmethod
    async def on_message_error(
        self, message: Message, exception: Exception
    ) -> None: ...
