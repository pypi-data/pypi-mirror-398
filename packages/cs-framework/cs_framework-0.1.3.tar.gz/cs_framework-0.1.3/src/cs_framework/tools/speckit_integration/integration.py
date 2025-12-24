import os
import sys
from loguru import logger

def read_template(filename):
    """Reads a template file from the templates directory relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "templates", filename)
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        return None
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def run_integration():
    """
    Integrates C-S Framework instructions into the local .specify configuration.
    This script is idempotent and safe to run multiple times.
    """
    logger.info("Starting Spec-Kit integration...")
    
    # 1. Update .specify/memory/constitution.md (Constitution)
    constitution_path = os.path.abspath(".specify/memory/constitution.md")
    csfw_rules = read_template("csfw_constitution.md")
    
    if csfw_rules:
        # Ensure directory exists
        os.makedirs(os.path.dirname(constitution_path), exist_ok=True)
        
        # Overwrite the constitution file with CSFW rules
        logger.info(f"Overwriting {constitution_path} with CSFW constitution...")
        with open(constitution_path, "w", encoding="utf-8") as f:
            f.write(csfw_rules)

    # 2. Update templates/plan-template.md
    plan_template_path = os.path.abspath(".specify/templates/plan-template.md")
    csfw_plan_section = read_template("csfw_plan_section.md")

    if csfw_plan_section and os.path.exists(plan_template_path):
        with open(plan_template_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "C-S Framework Architecture" not in content:
             # Insert before "## Project Structure"
            if "## Project Structure" in content:
                new_content = content.replace("## Project Structure", csfw_plan_section + "\n\n## Project Structure")
                logger.info(f"Adding CSFW section to {plan_template_path}...")
                with open(plan_template_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
            else:
                # Append if anchor not found
                logger.info(f"Appending CSFW section to {plan_template_path}...")
                with open(plan_template_path, "a", encoding="utf-8") as f:
                    f.write("\n" + csfw_plan_section)
        else:
            logger.info(f"CSFW section already present in {plan_template_path}.")

    # 3. Update templates/tasks-template.md
    tasks_template_path = os.path.abspath(".specify/templates/tasks-template.md")
    csfw_task_note = read_template("csfw_task_note.md")

    if csfw_task_note and os.path.exists(tasks_template_path):
        with open(tasks_template_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "CSFW Note" not in content:
            # Insert after "## Format:" section
            if "## Format:" in content:
                # Find the end of the format section (heuristic)
                insertion_point = content.find("## Path Conventions")
                if insertion_point != -1:
                    new_content = content[:insertion_point] + csfw_task_note + "\n" + content[insertion_point:]
                    logger.info(f"Adding CSFW note to {tasks_template_path}...")
                    with open(tasks_template_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                else:
                     with open(tasks_template_path, "a", encoding="utf-8") as f:
                        f.write("\n" + csfw_task_note)
            else:
                logger.info(f"Appending CSFW note to {tasks_template_path}...")
                with open(tasks_template_path, "a", encoding="utf-8") as f:
                    f.write("\n" + csfw_task_note)
        else:
            logger.info(f"CSFW note already present in {tasks_template_path}.")
    
    logger.success("Integration complete.")
