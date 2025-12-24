
import os
import json
import time

# Directory for virtual input file
INPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "virtual_key.json"))

def write_key(key_name: str):
    """
    Simulation of pressing a key by writing to a file.
    key_name: "UP", "DOWN", "LEFT", "RIGHT", "SPACE", "R", "Q"
    """
    data = {"key": key_name, "timestamp": time.time()}
    try:
        # Atomic write if possible, or simple write
        with open(INPUT_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing virtual key: {e}")

def read_key() -> str:
    """
    Read the virtual key and immediately clear it.
    Returns the key name or None.
    """
    if not os.path.exists(INPUT_FILE):
        return None
        
    try:
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
            
        # Consume the key (remove file)
        os.remove(INPUT_FILE)
        
        return data.get("key")
    except Exception:
        # File conflict or empty, ignore
        return None
