# DIALOGUS

## SYNOPSIS
A compositional framework for AI-based dialogue systems.

## DESCRIPTION
**Dialogus** is a facility for constructing complex conversational systems through the composition of simple, independent processing units. It provides a minimal set of primitives for message passing, transformation, and routing.

The complexity of modern AI applications often leads to brittle, entangled architectures. **Dialogus** posits that complex behavior emerges not from complex components, but from the rigorous composition of simple ones.

## PHILOSOPHY
The design of **dialogus** is informed by the Unix philosophy:

1.  Make each program do one thing well (composition over inheritance and monolithic design).
2.  Expect the output of every program to become the input to another, as yet unknown, program.
3.  Design and build software to be tried early, ideally within weeks.
4.  Write programs to handle a universal interface.
5.  Economy and elegance of design due to constraints ("salvation through suffering").
6.  Make it easy to write, test, and run programs.
7.  Self-supporting system: our system is maintained by itself.
8.  Do not attempt to predict user needs; provide the primitives with which users can solve their own problems. 

## ARCHITECTURE

The system maps the concepts of Information Theory onto three fundamental primitives.

### 1. MESSAGE

**NAME**

Message — the immutable quantum of information.

**SYNOPSIS**

```python
Message:
    content: Any
    id: str
    name: str
    timestamp: int
```

**DESCRIPTION**

A `Message` is a typed, immutable value object serving as the sole unit of exchange between processors.

In **dialogus**, "everything is a Message" (just as in Unix "everything is a file"). A `Message` is a discrete, self-identifying packet of typed data.

It is strictly immutable. State is never mutated in place; it is transformed by creating new `Messages`. This immutability guarantees that the history of a conversation is a perfect, append-only log of information states.

- **Identity**: Unique ID and timestamp.
- **Type**: Explicit class definition (e.g., `UserQuery`, `LLMResponse`) used for routing.
- **Payload**: Rigid, immutable.

### 2. PROCESSOR

**NAME**

Processor — the information channel.

**SYNOPSIS**

```python
Processor[MessageIn, MessageOut]:
    task_manager: Optional[TaskManager]
    observers: Optional[list[BaseObserver]]
```

**DESCRIPTION**

A `Processor` is a noisy channel that accepts a `Message`, performs work, and produces a new `Message`. It is the atom of computation, equivalent to a Unix filter.

The interface is polymorphic. To the framework, there is no distinction between an LLM, a database query, a REST API call, or a conditional logic block. They are all simply `Processors`.

- Input: Accepts exactly one `Message`. The input type is declared via the generic parameter `MessageIn`.
- Output: Returns exactly one `Message`. The output type is declared via the generic parameter `MessageOut`.
- Union Types: Union types are supported for both input and output types.
- Type Inference: Input and output types are extracted automatically from the generic parameters at construction time. No manual specification required.
- State: While the *interface* is functional, the *implementation* may be stateful (e.g., maintaining chat history or buffer windows).
- TaskManager: The `Processor` can optionally receive a `TaskManager` at construction time. If not provided, the `Composite` will propagate its own `TaskManager` to the `Processor`.

### 3. COMPOSITE

**NAME**

Composite — the information topology.

**SYNOPSIS**

```python
Composite[Message, Message]:
    processors: Sequence[Processor]
    max_hops: int = 30
```

**DESCRIPTION**

A `Composite` is a `Processor` that routes messages through a directed graph of processors. It is the Unix pipeline: a composition of filters where the output of one becomes the input of the next.

The routing logic is deterministic and type-driven. Given a `Message`, the `Composite` looks up its type in an internal mapping (derived from each processor's generic input types) and dispatches it to the corresponding `Processor`. The result is fed back into the system until a terminal condition is reached.

- Routing: Message type → `Processor` lookup. The mapping is built automatically from each processor's declared `MessageIn` type.
- Chaining: `Processor` output becomes the next input. The chain continues until termination.
- Termination: The loop exits when a `Processor` emits an `EgressMessage`.
- Bounds: A `max_hops` limit prevents infinite loops.
- TaskManager Propagation: The `Composite` propagates its `TaskManager` to child processors that lack one.

The `Topology` is a compiled representation of the routing graph. At construction time, it validates two invariants:

1. Completeness: Every output type produced by a processor must be handled by some processor in the topology.
2. Termination: At least one processor must produce an `EgressMessage`.

If either invariant is violated, the topology refuses to compile.

## INSTALLATION
```bash
pip install dialogus
```

## STANDARDS
The aesthetic of the project is industrial. We build tools for engineers, not consumers.

- **Boring:** Code should be predictable and standard. Excitement in code is usually a synonym for error.
- **Minimal:** If a feature can be implemented in user-space, it does not belong in the kernel (core).
- **Explicit:** Magic is forbidden. Control flow must be visible.