from dataclasses import dataclass, field
from typing import Sequence

from loguru import logger

from dialogus.messages.message import EgressMessage, Message
from dialogus.processors.processor import Processor


@dataclass(frozen=True)
class Topology:
    processors: Sequence[Processor]
    mapping: dict[type[Message], Processor] = field(init=False)

    def __post_init__(self):
        mapping = dict[type[Message], Processor]()
        for processor in self.processors:
            for input_type in processor.input_types:
                mapping[input_type] = processor
        object.__setattr__(self, "mapping", mapping)

        self._validate()

    def _validate(self):
        has_terminal = False
        handled_types = set[type[Message]](self.mapping.keys())
        unhandled = set[type[Message]]()

        for processor in self.processors:
            for output_type in processor.output_types:
                if issubclass(output_type, EgressMessage):
                    has_terminal = True
                elif output_type not in handled_types:
                    unhandled.add(output_type)

        if unhandled:
            raise ValueError(
                f"Unhandled message types: [{unhandled}]. None of {self.processors} handle these types."
            )
        if not has_terminal:
            raise ValueError(
                f"No terminal processor found. None of [{self.processors}] produce an EgressMessage."
            )

        logger.debug("Topology compiled:")
        for processor in self.processors:
            inputs = ", ".join(t.__name__ for t in processor.input_types)
            outputs = ", ".join(t.__name__ for t in processor.output_types)
            logger.debug(
                f"  [{processor.name}] - Inputs: {{{inputs}}} -> Outputs: {{{outputs}}}"
            )
