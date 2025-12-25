import json
from pathlib import Path
from typing import Dict, Any

def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Writes a Python dictionary to a file as JSON.

    Args:
        data (dict): Dictionary to write.
        file_path (str): File path to write to (default: 'canstate.txt').
    """
    path = Path(file_path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Reads a JSON dictionary from a file.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        dict: The parsed dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)