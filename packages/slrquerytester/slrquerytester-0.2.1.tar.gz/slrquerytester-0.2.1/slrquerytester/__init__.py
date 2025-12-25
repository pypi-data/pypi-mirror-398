from pathlib import Path

# Locate the README file relative to this file.
readme_path = Path(__file__).resolve().parent.parent / "README.md"

# Read all lines from the file.
with readme_path.open(encoding="utf-8") as f:
    lines = f.readlines()

# Define markers (or any filtering logic) to omit certain sections.
start_marker = "<!-- start omit -->"
end_marker = "<!-- end omit -->"
omit = False
filtered_lines = []
for line in lines:
    if start_marker in line:
        omit = True
        continue  # Skip the line with the start marker.
    if end_marker in line:
        omit = False
        continue  # Skip the line with the end marker.
    if not omit:
        filtered_lines.append(line)

# Combine the filtered lines into a single string.
__doc__ = "".join(filtered_lines)

import logging

logger = logging.getLogger("slrquerytester")

# Create and add a handler if it doesn't exist
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
