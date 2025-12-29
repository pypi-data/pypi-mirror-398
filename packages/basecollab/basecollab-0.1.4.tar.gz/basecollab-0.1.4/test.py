import json
import os

import basecollab

raw = basecollab.scan_py(
    selected_dirs=None,
    excluded_dirs=None,
    excluded_extensions=None,
    file_size_limit_mb=None,
)
data = json.loads(raw)
count = sum(len(section.get("children", [])) for section in data)
print(f"Found {count} TODOs")
print(json.dumps(data, indent=2))

