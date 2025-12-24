---
description: Generates Python code for new C-S Framework Concepts based on natural language specifications.
---

# Architect Workflow

Scaffolds new Concept classes for the C-S Framework.

## Usage

Use this workflow when you need to create a new Concept.

## CLI Command

// turbo-all

```bash
csfw scaffold <ConceptName> --actions <action1> <action2> --events <event1> <event2> --output <output_dir>
```

### Parameters

- `name` (required): The name of the Concept class (e.g., "Player")
- `--actions` / `-a`: List of action names to generate methods for
- `--events` / `-e`: List of event names this concept will emit
- `--output` / `-o`: Directory to save the file (default: current directory)

### Example

```bash
csfw scaffold Player --actions move attack die --events moved attacked died --output src/examples/roguelike/src/concepts/
```

This generates a Python file with:
- Class definition extending `Concept`
- Pydantic event models
- Action method stubs
- Event registration
