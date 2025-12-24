import json
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
def load_platform(file_path, categories=None, exclude=None, specific=None):

    file_path = BASE_DIR / "platforms.json"
    with open(file_path, 'r') as f:
        full_data = json.load(f)

    # If your JSON has a top-level "platforms" key, use that data
    # Otherwise, use the whole file
    data = full_data.get('platforms', full_data)

    filtered = {}
    cat_list = [c.strip() for c in categories.split(',')] if categories else []
    excl_list = [e.strip() for e in exclude.split(',')] if exclude else []
    spec_list = [s.strip() for s in specific.split(',')] if specific else []

    for name, info in data.items():
        # Skip if 'info' isn't a dictionary (like if it's a version number string)
        if not isinstance(info, dict): continue

        if spec_list and name not in spec_list: continue
        if excl_list and name in excl_list: continue
        if cat_list and info.get('category') not in cat_list: continue

        filtered[name] = info

    return filtered

def load_usernames(filepath):
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]
