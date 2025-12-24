import ast
import os
from typing import List, Dict, Set, Any, Optional
from loguru import logger

class ConceptDef:
    def __init__(self, name: str):
        self.name = name
        self.actions: Set[str] = set()
        self.events: Set[str] = set()

class Linter:
    def __init__(self):
        self.concepts: Dict[str, ConceptDef] = {}
        self.synchronizations: List[Dict[str, str]] = []

    def analyze_workspace(self, root_path: str):
        # Pass 1: Find all Concept definitions
        self._scan_directory(root_path, self._pass_find_concepts)
        # Pass 2: Find all Synchronizations
        self._scan_directory(root_path, self._pass_find_syncs)

    def _scan_directory(self, root_path: str, callback):
        if os.path.isfile(root_path):
             callback(root_path)
             return

        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith(".py"):
                    callback(os.path.join(root, file))

    def _pass_find_concepts(self, file_path: str):
        tree = self._parse_file(file_path)
        if not tree: return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_class(node)

    def _pass_find_syncs(self, file_path: str):
        tree = self._parse_file(file_path)
        if not tree: return
        
        # Local variables for this file (tracking instances)
        variables: Dict[str, str] = {} # var_name -> class_name

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                self._analyze_assignments(node, variables)
            elif isinstance(node, ast.Call):
                self._analyze_synchronization_instantiation(node, variables)

    def _parse_file(self, file_path: str) -> Optional[ast.AST]:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return ast.parse(f.read(), filename=file_path)
            except SyntaxError:
                logger.error(f"Syntax error in {file_path}")
                return None

    def _analyze_class(self, node: ast.ClassDef):
        is_concept = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Concept":
                is_concept = True
            elif isinstance(base, ast.Attribute) and base.attr == "Concept":
                is_concept = True
        
        if not is_concept:
            return

        concept = ConceptDef(node.name)
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if not item.name.startswith("_"):
                    concept.actions.add(item.name)
                
                # Check for emit calls
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Call):
                        if isinstance(stmt.func, ast.Attribute) and stmt.func.attr == "emit":
                            # Check if called on self
                            if isinstance(stmt.func.value, ast.Name) and stmt.func.value.id == "self":
                                if stmt.args:
                                    arg0 = stmt.args[0]
                                    if isinstance(arg0, ast.Constant): # Python 3.8+
                                        concept.events.add(arg0.value)
                                    elif isinstance(arg0, ast.Str): # Python < 3.8
                                        concept.events.add(arg0.s)

        self.concepts[node.name] = concept

    def _analyze_assignments(self, node: ast.Assign, variables: Dict[str, str]):
        # Track variable assignments: var = Class("Name")
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id
                # Heuristic: If class_name matches a known Concept, track it
                if class_name in self.concepts:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables[target.id] = class_name

    def _analyze_synchronization_instantiation(self, node: ast.Call, variables: Dict[str, str]):
        # Check for Synchronization(...)
        if isinstance(node.func, ast.Name) and node.func.id == "Synchronization":
            source_concept = None
            event_name = None
            target_actions = [] # List of (target_concept, action_name)

            for keyword in node.keywords:
                if keyword.arg == "when":
                    # Expect EventPattern(...)
                    if isinstance(keyword.value, ast.Call) and isinstance(keyword.value.func, ast.Name) and keyword.value.func.id == "EventPattern":
                        ep_args = keyword.value.args
                        ep_keywords = keyword.value.keywords
                        
                        # Positional
                        if len(ep_args) >= 2:
                            if isinstance(ep_args[0], ast.Name):
                                source_concept = variables.get(ep_args[0].id)
                            if isinstance(ep_args[1], ast.Constant):
                                event_name = ep_args[1].value
                            elif isinstance(ep_args[1], ast.Str):
                                event_name = ep_args[1].s
                        
                        # Keyword
                        for k in ep_keywords:
                            if k.arg == "source_concept":
                                if isinstance(k.value, ast.Name):
                                    source_concept = variables.get(k.value.id)
                            elif k.arg == "event_name":
                                if isinstance(k.value, ast.Constant):
                                    event_name = k.value.value
                                elif isinstance(k.value, ast.Str):
                                    event_name = k.value.s

                elif keyword.arg == "then":
                    # Expect list of ActionInvocation
                    if isinstance(keyword.value, ast.List):
                        for item in keyword.value.elts:
                            if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "ActionInvocation":
                                t_concept = None
                                a_name = None
                                
                                ai_args = item.args
                                ai_keywords = item.keywords
                                
                                # Positional
                                if len(ai_args) >= 2:
                                    if isinstance(ai_args[0], ast.Name):
                                        t_concept = variables.get(ai_args[0].id)
                                    if isinstance(ai_args[1], ast.Constant):
                                        a_name = ai_args[1].value
                                    elif isinstance(ai_args[1], ast.Str):
                                        a_name = ai_args[1].s
                                
                                # Keyword
                                for k in ai_keywords:
                                    if k.arg == "target_concept":
                                        if isinstance(k.value, ast.Name):
                                            t_concept = variables.get(k.value.id)
                                    elif k.arg == "action_name":
                                        if isinstance(k.value, ast.Constant):
                                            a_name = k.value.value
                                        elif isinstance(k.value, ast.Str):
                                            a_name = k.value.s
                                
                                if t_concept and a_name:
                                    target_actions.append((t_concept, a_name))

            if source_concept and event_name and target_actions:
                for t_concept, a_name in target_actions:
                    self.synchronizations.append({
                        "source": source_concept,
                        "event": event_name,
                        "target": t_concept,
                        "action": a_name
                    })

    def report(self):
        print("Analysis Report:")
        print("----------------")
        for name, concept in self.concepts.items():
            print(f"Concept: {name}")
            print(f"  Actions: {', '.join(sorted(concept.actions))}")
            print(f"  Events: {', '.join(sorted(concept.events))}")
        
        print("\nSynchronizations:")
        print("-----------------")
        for sync in self.synchronizations:
            print(f"  {sync['source']}.{sync['event']} -> {sync['target']}.{sync['action']}")

        print("\nIssues:")
        print("-------")
        self._check_issues()

    def _check_issues(self):
        # 1. Undefined Actions
        for sync in self.synchronizations:
            target_concept = self.concepts.get(sync['target'])
            if target_concept:
                if sync['action'] not in target_concept.actions:
                    logger.error(f"Undefined Action: '{sync['action']}' in concept '{target_concept.name}' (referenced by sync from {sync['source']})")
            else:
                # Could not resolve target concept class
                pass

        # 2. Disconnected Events
        all_synced_events = set()
        for sync in self.synchronizations:
            all_synced_events.add(sync['event'])
            
        for name, concept in self.concepts.items():
            for event in concept.events:
                if event not in all_synced_events:
                    logger.warning(f"Disconnected Event: '{event}' in concept '{name}' is never synchronized.")

def run_linter(path: str):
    linter = Linter()
    linter.analyze_workspace(path)
    linter.report()

def main():
    import sys
    if len(sys.argv) > 1:
        run_linter(sys.argv[1])
    else:
        print("Usage: csfw lint <path_to_scan>")

if __name__ == "__main__":
    main()
