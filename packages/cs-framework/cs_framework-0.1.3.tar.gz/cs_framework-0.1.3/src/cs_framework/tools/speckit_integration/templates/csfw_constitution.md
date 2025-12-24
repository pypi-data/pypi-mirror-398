# Project Constitution
## C-S Framework Integration Rules
You are operating within a project that uses the **Concept-Synchronization Framework (CSFW)**.
You MUST adhere to the following rules when planning and implementing features:
1.  **Architecture Compliance**:
    *   All logic must be encapsulated in **Concepts** (`src/concepts/*.py`).
    *   Concepts communicate ONLY via **Events**.
    *   Interactions between Concepts are defined in **Synchronization Rules** (`src/sync/rules.yaml`).
    *   Do NOT write spaghetti code or tightly coupled classes.
2.  **Tool Usage (Mandatory)**:
    You MUST use the specific `csfw` commands defined in the workflows:
    *   **Scaffolding** (`/csfw-architect`): ...
    *   **Validation** (`/csfw-linter`): ...
    *   **Testing** (`/csfw-fuzzer`): ...
    *   **Debugging** (`/csfw-debugger`): ...
    *   **Code Search** (`/ast-grep`): Use AST-based search for smart code lookup/replacement:
        `ast-grep --pattern <pattern> --lang <lang> <path>`
    *   **Development Guide** (`/csfw-dev`): Refer to this workflow for the complete end-to-end development process.
3.  **Implementation Flow**:
    *   **Plan Phase**: Define Concepts, Events, and Sync Rules in `plan.md`.
    *   **Task Phase**: Create tasks for scaffolding, implementing logic, and defining sync rules.
    *   **Implement Phase**: Execute the tasks using the CSFW tools.