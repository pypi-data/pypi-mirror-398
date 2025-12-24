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
8.  We do not attempt to predict user needs; we provide the primitives with which users can solve their own problems. 
9.  Simplicity > explicitness > complexity > cleverness.

## ARCHITECTURE

The system maps the abstract concepts of Information Theory onto three fundamental primitives.

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
Processor:
    task_manager: TaskManager
    output_types: Optional[set[type[Message]]]
    observers: Optional[list[BaseObserver]]
```

**DESCRIPTION**

A `Processor` is a noisy channel that accepts a `Message`, performs work, and produces a new `Message`. It is the atom of computation, equivalent to a Unix filter.

The interface is polymorphic. To the framework, there is no distinction between an LLM, a database query, a REST API call, or a conditional logic block. They are all simply `Processors`.

- **Input**: Accepts exactly one `Message`.
- **Output**: Returns exactly one `Message`.
- **State**: While the *interface* is functional, the *implementation* may be stateful (e.g., maintaining chat history or buffer windows).

### 3. COMPOSITE

**NAME**

Composite — the information topology.

**SYNOPSIS**

```python
Composite:
    handlers: dict[type[Message], Processor]
    max_hops: int = 30
```

**DESCRIPTION**

The `Composite` is a `Processor` that contains other processors. It does not perform work itself; it routes information.

Routing is **Type-Based**. The `Composite` maintains a routing table mapping `InputType -> Processor`. When a message enters the `Composite`, it is inspected, routed to the matching handler, and the result is re-evaluated for the next route.

**MECHANICS**

- **1:1 Routing**: Each `Message` type has exactly one handler in a given `Composite` context.
- **Recursion**: Since a `Composite` is a `Processor`, it can be nested within other `Composites`, allowing for fractal architectures (Agents within Agents).
- **Termination**: Flow stops when a processor returns an `EgressMessage` is produced, or the `max_hops` limit is reached.

## STANDARDS
The aesthetic of the project is industrial. We build tools for engineers, not consumers.

- **Boring:** Code should be predictable and standard. Excitement in code is usually a synonym for error.
- **Minimal:** If a feature can be implemented in user-space, it does not belong in the kernel (core).
- **Explicit:** Magic is forbidden. Control flow must be visible.