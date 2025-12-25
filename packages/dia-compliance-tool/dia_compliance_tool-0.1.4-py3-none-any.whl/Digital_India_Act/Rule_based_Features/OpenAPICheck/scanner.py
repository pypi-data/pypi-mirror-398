import os
from typing import List

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".cs"}

def scan_source_files(root_dir: str) -> List[str]:
    files = []
    for root, _, filenames in os.walk(root_dir):
        for file in filenames:
            ext = os.path.splitext(file)[1]
            if ext in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, file))

    return files