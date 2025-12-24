import sys
import os
import argparse
import importlib.util
import yaml
import json
from cs_framework.engine.scenario import ScenarioPlayer

def load_runner(setup_path):
    if not os.path.exists(setup_path):
        raise FileNotFoundError(f"Setup file not found: {setup_path}")

    spec = importlib.util.spec_from_file_location("app_setup", setup_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["app_setup"] = module
    spec.loader.exec_module(module)

    if hasattr(module, "runner"):
        return module.runner
    elif hasattr(module, "get_runner"):
        return module.get_runner()
    else:
        raise ValueError("Setup file must define 'runner' variable or 'get_runner' function.")

def load_scenario(scenario_path):
    if not os.path.exists(scenario_path):
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    with open(scenario_path, 'r', encoding='utf-8') as f:
        if scenario_path.endswith('.yaml') or scenario_path.endswith('.yml'):
            return yaml.safe_load(f)
        elif scenario_path.endswith('.json'):
            return json.load(f)
        else:
            raise ValueError("Scenario file must be .yaml or .json")

def run_scenario_tool(setup_file, scenario_file):
    try:
        print(f"Loading runner from {setup_file}...")
        runner = load_runner(setup_file)

        print(f"Loading scenario from {scenario_file}...")
        scenario = load_scenario(scenario_file)

        print("Starting scenario execution...")
        runner.start()
        player = ScenarioPlayer(runner)
        player.play(scenario)

        print("Scenario completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run a scenario against a C-S Framework application.")
    parser.add_argument("setup_file", help="Path to Python file that exports 'runner' or 'get_runner()'")
    parser.add_argument("scenario_file", help="Path to YAML/JSON scenario file")

    args = parser.parse_args()
    run_scenario_tool(args.setup_file, args.scenario_file)

if __name__ == "__main__":
    main()
