---
description: Tools for running test scenarios and fuzzing the application.
---

# Fuzzer Workflow

Executes predefined scenarios (sequences of actions) to verify behavior or test edge cases.

## Use Cases

- Verify that a specific sequence of actions leads to the expected state
- Reproduce a bug by running a specific scenario
- Stress-test the system with edge-case sequences

## CLI Command

// turbo-all

```bash
csfw run-scenario <setup_file> <scenario_file>
```

### Parameters

- `setup_file` (required): Path to Python file that exports `runner` variable or `get_runner()` function
- `scenario_file` (required): Path to YAML/JSON scenario file

### Example

```bash
csfw run-scenario src/examples/pacman/run.py src/examples/pacman/scenario_test.yaml
```

## Scenario File Format

```yaml
# scenario_test.yaml
- type: dispatch
  target: Player
  action: move
  payload:
    direction: "RIGHT"

- type: assert_state
  target: Player
  expected_state:
    x: 1
    y: 0

- type: wait
  ticks: 5
```

### Step Types

| Type | Description |
|------|-------------|
| `dispatch` | Trigger an action on a concept |
| `assert_state` | Verify the state of a concept |
| `wait` | Wait for N ticks (logical time) |
