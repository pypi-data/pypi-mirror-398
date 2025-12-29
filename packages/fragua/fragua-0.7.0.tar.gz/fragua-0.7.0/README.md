# Fragua

**Fragua** is a modular Python library for modeling and orchestrating **ETL / ELT workflows** through explicit execution environments, strong domain boundaries, and a centralized orchestration model.

Fragua is designed as an educational and experimental framework focused on **clarity of architecture**, **predictable execution**, and **explicit responsibility separation**.

---

## Core Concept

In Fragua, **everything happens inside an Environment**.

An `Environment` represents an isolated execution context that owns:

- Component lifecycle and configuration
- Security and execution boundaries
- Runtime state and metadata
- Data persistence and traceability

Agents do not exist or operate independently.  
They are created, configured, and executed exclusively within an Environment.

---

## Environment Responsibilities

The `Environment` is the central orchestrator of the system. It is responsible for:

- Initializing the **Warehouse**
- Managing action contexts: `extract`, `transform`, `load`
- Registering and resolving all components
- Enforcing security and execution boundaries
- Providing a unified API for component lifecycle management
- Exposing a structured summary of the runtime state

Multiple environments can coexist, each representing a separate pipeline, experiment, or workflow.

---

## Unified Component Management

All components in Fragua are managed through a **single, unified CRUD API** exposed by the Environment.

Components are always resolved by:

- **Action** (`extract`, `transform`, `load`)
- **Component type** (`agent`, `params`, `function`, `style`)

This applies consistently to all operations:

- Create
- Read
- Update
- Delete

This design avoids duplicated logic, reduces coupling, and guarantees consistent behavior across the system.

---

## Agents and Execution Model

Fragua defines three agent roles:

- **Extractor** — Retrieves data from external sources
- **Transformer** — Applies transformations or enrichment logic
- **Loader** — Persists or delivers processed data

Agents:

- Are instantiated exclusively by the Environment
- Receive mandatory execution credentials
- Resolve configuration only through registered components
- Interact with data exclusively via the Warehouse
- Follow a standardized execution workflow

Agents act as controlled executors, not as owners of state or configuration.

---

## Security Model

Fragua enforces an explicit internal security model:

- The **Environment** issues execution credentials
- **Agents** consume credentials to operate
- The **Warehouse** validates credentials for protected operations

This guarantees that no agent can execute or access data outside a valid environment context.

---

## Domain-Driven Typing

Fragua uses a strongly typed, enum-based domain vocabulary.

Enums define all core concepts, including:

- Actions and component types
- Agent roles
- Storage and target types
- Operations, fields, and attributes

This approach:

- Eliminates magic strings
- Centralizes validation
- Improves IDE support and static analysis
- Provides a clear and extensible domain language

Concise enum aliases are exported for ergonomic usage without sacrificing type safety.

---

## Component Architecture

Fragua follows a layered component model:

- **FraguaComponent**  
  Base abstraction for all registrable elements.

- **FraguaSet**  
  Generic in-memory container responsible for:
  - CRUD operations
  - Validation
  - Summaries

- **FraguaRegistry**  
  Runtime structure that groups multiple `FraguaSet` instances
  by action and component type.

This separation ensures clarity between existence, organization, and orchestration.

---

## Warehouse and Data Traceability

Each Environment owns a **Warehouse**, which acts as the single source of truth for data artifacts.

The Warehouse provides:

- Controlled data operations
- Full movement logging with timestamps
- Undo support for destructive actions
- Metadata-based summaries and inspection

---

## Key Characteristics

- Environment-centric orchestration
- Unified component lifecycle management
- Explicit security boundaries
- Strongly typed domain model
- Isolated execution contexts
- Centralized storage and traceability
- Clear separation of responsibilities

---

## Project Structure



## Project Structure

```
fragua/
├── core/
├── environments/
├── extract/
├── transform/
├── load/
├── utils/
└── __init__.py
```

---

## Installation

```bash
python -m pip install -e .
```

> ⚠️ Fragua is published on PyPI for learning purposes.  
> It is **not recommended for production use yet**.

---

## Author

**Santiago Lanz**  
🌐 https://sagodev.github.io/Portfolio-Web-Santiago-Lanz/  
💼 https://www.linkedin.com/in/santiagolanz/  
🐙 https://github.com/SagoDev  

---

## License

MIT License
