---
description: C-S Framework development workflow - the complete guide for building CSFW applications.
---

# CSFW Development Workflow

This workflow guides you through the complete process of developing applications using the Concept-Synchronization Framework.

## Overview

CSFW applications are built using:
- **Concepts**: Encapsulated logic units with state and actions
- **Events**: Messages emitted by Concepts to communicate
- **Synchronization Rules**: YAML-defined mappings from events to actions

## Development Flow

// turbo-all

### 1. Design Phase

Before coding, define your Concepts, their actions, events, and synchronization rules.

```
Concept: Player
  Actions: move, attack, take_damage, die
  Events: moved, attacked, damaged, died

Concept: Monster  
  Actions: ai_move, attack, take_damage, die
  Events: moved, attacked, damaged, died

Synchronization:
  Player.attacked -> Combat.resolve_attack
  Combat.damage_dealt -> Monster.take_damage
  Monster.died -> Player.gain_exp
```

### 2. Scaffold Concepts

Use `/csfw-architect` to generate concept files:

```bash
csfw scaffold Player --actions move attack take_damage die --events moved attacked damaged died --output src/concepts/
csfw scaffold Monster --actions ai_move attack take_damage die --events moved attacked damaged died --output src/concepts/
```

### 3. Implement Logic

Edit the generated files in `src/concepts/`:
- Fill in action method logic
- Update state management
- Emit events with appropriate payloads

### 4. Define Synchronization Rules

Create `src/sync/rules.yaml`:

```yaml
synchronizations:
  - name: PlayerAttack
    when:
      source: Player
      event: attacked
    then:
      - target: Combat
        action: resolve_attack
        payload:
          attacker: event.source
          target_x: event.target_x
          target_y: event.target_y
```

### 5. Validate with Linter

Use `/csfw-linter` to check for issues:

```bash
csfw lint --path src/
```

This detects:
- Undefined actions referenced in sync rules
- Disconnected events (emitted but never synchronized)

### 6. Test with Scenarios

Use `/csfw-fuzzer` to run test scenarios:

```bash
csfw run-scenario run.py scenario_test.yaml
```

### 7. Debug with Logs

Use `/csfw-debugger` to analyze execution:

```bash
csfw gui --log execution.ttl
csfw gui --log execution.ttl
```

### 8. Autonomous Testing with RDF/SPARQL

For advanced testing and debugging, you can control the application externally using RDF/SPARQL without a GUI or manual input.

#### Workflow
1. **Enable RDF Command Polling**: Ensure your `Runner` or Game Loop checks for pending commands in the RDF Logger.
2. **External Agent**: Create a script that acts as a "Driver".
    - **Read State**: Query the latest game state from the RDF Graph using SPARQL (e.g., "Select Player position").
    - **Think**: Use logic or LLM to decide the next action.
    - **Act**: Write command triples (e.g., `Player a:move ...`) to the command `.ttl` file.
3. **Loop**: The game reads the command, executes it, updates the state, and the cycle repeats.

This allows for:
- **Headless E2E Testing**: Run the full game logic driven by an agent.
- **Fuzzing with Context**: Generate inputs based on available actions in the current state.
- **AI Debugging**: Let an LLM play the game to find edge cases.

#### Example Architecture
`Driver Script` <--(SPARQL Queries)-- `RDF Graph (State)` <--(Updates)-- `Game Process`
`Driver Script` --(RDF Commands)--> `Command File` --(Polling)--> `Game Process`

## Project Structure

```
my_csfw_app/
├── run.py                 # Runner setup
├── main.py                # Entry point (GUI/CLI)
├── src/
│   ├── concepts/          # Concept classes
│   │   ├── player.py
│   │   ├── monster.py
│   │   └── ...
│   └── sync/
│       └── rules.yaml     # Synchronization rules
├── scenario_test.yaml     # Test scenarios
└── execution.ttl          # Execution log (generated)
```

## Quick Reference

| Task | Command |
|------|---------|
| Create new Concept | `csfw scaffold <Name> --actions ... --events ... --output ...` |
| Validate structure | `csfw lint --path src/` |
| Run test scenario | `csfw run-scenario run.py scenario.yaml` |
| Debug execution | `csfw gui --log execution.ttl` |
