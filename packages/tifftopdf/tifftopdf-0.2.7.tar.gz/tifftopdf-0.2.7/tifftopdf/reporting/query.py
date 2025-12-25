from __future__ import annotations

import json
import os
from typing import List

def get_processed_batches(output_root: str, meta_subdir: str = "metadata") -> List[str]:
    """
    Scans the metadata directory for batch JSON files and returns a list of 
    batch names that were successfully processed.
    """
    meta_path = os.path.join(output_root, meta_subdir)
    if not os.path.isdir(meta_path):
        return []

    processed = []
    
    # Iterate over all files in the metadata directory
    with os.scandir(meta_path) as it:
        for entry in it:
            if not entry.is_file() or not entry.name.endswith(".json"):
                continue
            
            # Skip global run metadata and state file
            if entry.name in ("run.json", "run_state.json"):
                continue
                
            try:
                with open(entry.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Check if the batch was successful
                if data.get("success") is True:
                    # Use the batch_name from the JSON if available, otherwise derive from filename
                    batch_name = data.get("batch_name")
                    if not batch_name:
                        batch_name = entry.name[:-5] # remove .json
                    processed.append(batch_name)
            except (json.JSONDecodeError, OSError):
                # Ignore malformed files or read errors
                continue
                
    return sorted(processed)
