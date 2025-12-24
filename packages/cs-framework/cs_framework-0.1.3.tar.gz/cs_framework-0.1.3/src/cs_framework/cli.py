import argparse
import os
import shutil
import sys
# import pkg_resources # Deprecated
import importlib.resources
from .tools.architect import generate_concept
from .tools.speckit_integration import run_integration
from .tools.linter import run_linter
from .tools.scenario_runner import run_scenario_tool

# For GUI, it's in src/cs_gui/main.py. This is outside cs_framework package usually?
# In setup.py: packages=find_packages(where="src"), package_dir={"": "src"}
# So cs_gui is a top level package.
try:
    from cs_gui.main import run_gui
except ImportError:
    run_gui = None

def install_skills(args):
    target_dir = args.target
    tool = getattr(args, 'tool', 'claude')
    
    # Tool-specific default paths
    default_paths = {
        'claude': os.path.join(os.getcwd(), ".claude", "skills", "csfw"),
        'antigravity': os.path.join(os.getcwd(), ".agent", "workflows"),
    }
    
    # If target is not specified, use tool-specific default
    if not target_dir:
        target_dir = default_paths.get(tool, default_paths['claude'])

    print(f"Installing skills for {tool} to: {target_dir}")

    # Get the path to the bundled skills directory
    try:
        # Modern way using importlib.resources
        # Assuming python 3.9+
        if sys.version_info >= (3, 9):
            source_dir = importlib.resources.files('cs_framework').joinpath('skills')
        else:
            # Fallback for older python or if not installed as package
            source_dir = os.path.join(os.path.dirname(__file__), 'skills')
    except Exception:
        source_dir = os.path.join(os.path.dirname(__file__), 'skills')

    # Convert Traversable to path string if needed
    if hasattr(source_dir, 'joinpath'): 
         # It's a Traversable, we need to iterate or copy from it. 
         # But for simplicity in this script, let's assume file system access or use as_file
         # For now, let's stick to the simple os.path fallback if it's a local script
         pass
    
    # Re-evaluating source_dir for simplicity in this context
    # Since we are likely running from source or simple install
    source_dir_path = str(source_dir)
    if not os.path.exists(source_dir_path):
         # Try relative path
         source_dir_path = os.path.join(os.path.dirname(__file__), 'skills')

    if not os.path.exists(source_dir_path):
        print(f"Error: Skills directory not found at {source_dir_path}")
        sys.exit(1)

    try:
        os.makedirs(target_dir, exist_ok=True)
        
        if tool == 'antigravity':
            # Convert SKILL.md to Antigravity workflow format
            _install_for_antigravity(source_dir_path, target_dir)
        else:
            # Claude: copy skill directories as-is
            _install_for_claude(source_dir_path, target_dir)
        
        print("\nSuccess! Skills installed.")
        if tool == 'claude':
            print("Please restart Claude Desktop to load the new skills.")
        elif tool == 'antigravity':
            print("Workflows are now available. Use /csfw-<skill_name> to invoke them.")
        
    except Exception as e:
        print(f"Error installing skills: {e}")
        sys.exit(1)


def _install_for_claude(source_dir_path: str, target_dir: str):
    """Copy skill directories as-is for Claude."""
    for item in os.listdir(source_dir_path):
        src_item_path = os.path.join(source_dir_path, item)
        if os.path.isdir(src_item_path):
            skill_md = os.path.join(src_item_path, "SKILL.md")
            if os.path.exists(skill_md):
                dst_item_path = os.path.join(target_dir, item)
                if os.path.exists(dst_item_path):
                    shutil.rmtree(dst_item_path)
                shutil.copytree(src_item_path, dst_item_path)
                print(f"  - Installed skill: {item}")


def _install_for_antigravity(source_dir_path: str, target_dir: str):
    """Copy SKILL.md files as workflow files for Antigravity.
    
    SKILL.md files are already in Antigravity workflow format
    (YAML frontmatter + Markdown with CLI commands).
    Also updates AGENTS.md with CSFW integration rules.
    """
    for item in os.listdir(source_dir_path):
        src_item_path = os.path.join(source_dir_path, item)
        if os.path.isdir(src_item_path):
            skill_md_path = os.path.join(src_item_path, "SKILL.md")
            if os.path.exists(skill_md_path):
                # Copy SKILL.md as csfw-<name>.md
                workflow_filename = f"csfw-{item}.md"
                workflow_path = os.path.join(target_dir, workflow_filename)
                shutil.copy2(skill_md_path, workflow_path)
                print(f"  - Installed workflow: {workflow_filename}")
    
    # Update AGENTS.md with CSFW rules
    _update_agents_md()


def _update_agents_md():
    """Append CSFW rules to AGENTS.md if not already present."""
    agents_md_path = os.path.join(os.getcwd(), "AGENTS.md")
    
    csfw_marker = "<!-- CSFW-INTEGRATION -->"
    csfw_rules = f'''
{csfw_marker}

## C-S Framework Integration

This project uses the **Concept-Synchronization Framework (CSFW)**.

### Architecture Rules

- All logic must be in **Concepts** (`src/concepts/*.py`)
- Concepts communicate ONLY via **Events**
- Interactions are defined in **Synchronization Rules** (`src/sync/rules.yaml`)

### Development Workflow

Use the CSFW workflows for development:

| Task | Workflow |
|------|----------|
| **Full development guide** | `/csfw-dev` |
| **Scaffold new Concept** | `/csfw-architect` |
| **Validate structure** | `/csfw-linter` |
| **Run test scenarios** | `/csfw-fuzzer` |
| **Debug execution** | `/csfw-debugger` |

### Quick Commands

```bash
# Create a new Concept
csfw scaffold Player --actions move attack --events moved attacked --output src/concepts/

# Validate the project
csfw lint --path src/

# Run a test scenario
csfw run-scenario run.py scenario_test.yaml
```
'''
    
    # Check if AGENTS.md exists
    if os.path.exists(agents_md_path):
        with open(agents_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if csfw_marker in content:
            print("  - AGENTS.md: CSFW rules already present (skipped)")
            return
        
        # Append to existing file
        with open(agents_md_path, 'a', encoding='utf-8') as f:
            f.write(csfw_rules)
        print("  - AGENTS.md: Appended CSFW integration rules")
    else:
        # Create new AGENTS.md
        with open(agents_md_path, 'w', encoding='utf-8') as f:
            f.write("# AGENTS.md\n\nProject-specific instructions for AI coding assistants.\n")
            f.write(csfw_rules)
        print("  - AGENTS.md: Created with CSFW integration rules")

def scaffold(args):
    generate_concept(
        name=args.name,
        actions=args.actions,
        events=args.events,
        output_dir=args.output
    )

def main():
    parser = argparse.ArgumentParser(description="C-S Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # install-skills command
    parser_skills = subparsers.add_parser("install-skills", help="Install skills for AI coding assistants")
    parser_skills.add_argument("--tool", choices=["claude", "antigravity"], default="claude",
                                help="Target tool (default: claude)")
    parser_skills.add_argument("--target", help="Target directory (default: tool-specific)")
    parser_skills.set_defaults(func=install_skills)

    # scaffold command
    parser_scaffold = subparsers.add_parser("scaffold", help="Scaffold a new Concept")
    parser_scaffold.add_argument("name", help="Name of the Concept class")
    parser_scaffold.add_argument("--actions", "-a", nargs="*", help="List of actions")
    parser_scaffold.add_argument("--events", "-e", nargs="*", help="List of events")
    parser_scaffold.add_argument("--output", "-o", default=".", help="Output directory")
    parser_scaffold.set_defaults(func=scaffold)

    # integrate-speckit command
    parser_speckit = subparsers.add_parser("integrate-speckit", help="Integrate CSFW with Spec-Kit")
    parser_speckit.set_defaults(func=lambda args: run_integration())

    # lint command
    parser_lint = subparsers.add_parser("lint", help="Run the CSFW Linter")
    parser_lint.add_argument("--path", default=".", help="Path to scan (default: .)")
    parser_lint.set_defaults(func=lambda args: run_linter(args.path))

    # run-scenario command
    parser_scenario = subparsers.add_parser("run-scenario", help="Run a scenario test")
    parser_scenario.add_argument("setup_file", help="Path to Python file that exports 'runner'")
    parser_scenario.add_argument("scenario_file", help="Path to YAML/JSON scenario file")
    parser_scenario.set_defaults(func=lambda args: run_scenario_tool(args.setup_file, args.scenario_file))

    # gui command
    if run_gui:
        parser_gui = subparsers.add_parser("gui", help="Run the Debugger GUI")
        parser_gui.add_argument("--log", default="execution.ttl", help="Path to the RDF log file")
        parser_gui.set_defaults(func=lambda args: run_gui(args.log))

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
