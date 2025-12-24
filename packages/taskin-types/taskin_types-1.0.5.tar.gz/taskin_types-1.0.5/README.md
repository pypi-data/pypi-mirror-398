# taskin-types

Python models automatically generated from Taskin TypeScript schemas.

## Installation

```bash
pip install taskin-types
```

## Usage

```python
from taskin_types import Task, User

# Use the Pydantic models
task = Task(
    id="task-001",
    title="Example Task",
    status="todo"
)
```

## Motivation

To enable Python packages to use the same data structures as the TypeScript packages, ensuring consistency across the Taskin ecosystem.

## Purpose

This package consumes the JSON schemas from `@taskin/types-ts` and uses `datamodel-codegen` to generate Pydantic models. This avoids manual duplication and reduces the risk of inconsistencies.
