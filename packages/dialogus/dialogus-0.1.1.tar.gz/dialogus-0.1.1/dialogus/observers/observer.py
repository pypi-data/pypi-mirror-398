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
    received_at: int


@dataclass(frozen=True)
class MessageProcessed(Message):
    source_processor: "Processor"
    source_message: Message
    processed_message: Message
    processed_at: int


@dataclass(frozen=True)
class MessageError(Message):
    source_processor: "Processor"
    source_message: Message
    exception: Exception
    error_at: int


class BaseObserver(ABC):
    @abstractmethod
    async def on_message_received(self, message: MessageReceived) -> None: ...

    @abstractmethod
    async def on_message_processed(self, message: MessageProcessed) -> None: ...

    @abstractmethod
    async def on_message_error(self, message: MessageError) -> None: ...
