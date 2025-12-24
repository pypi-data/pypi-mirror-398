---
description: Analyzes C-S Framework projects for structural issues like disconnected events or undefined actions.
---

# Linter Workflow

Statically analyzes your C-S Framework implementation for potential issues.

## Checks

- **Disconnected Events**: Events emitted by a Concept but never used in a Synchronization
- **Undefined Actions**: Actions referenced in a Synchronization that don't exist in the target Concept

## CLI Command

// turbo-all

```bash
csfw lint --path <directory_to_scan>
```

### Parameters

- `--path`: Root directory of the source code to analyze (default: current directory)

### Example

```bash
csfw lint --path src/examples/roguelike/src
```

### Output

```
Analysis Report:
----------------
Concept: Player
  Actions: attack, die, move
  Events: attacked, died, moved

Synchronizations:
-----------------
  Player.moved -> Board.update_position

Issues:
-------
WARNING: Disconnected Event: 'attacked' in concept 'Player' is never synchronized.
```
