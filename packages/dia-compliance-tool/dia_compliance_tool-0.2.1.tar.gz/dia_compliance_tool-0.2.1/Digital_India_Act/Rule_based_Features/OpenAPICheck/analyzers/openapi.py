import os
import re

OPENAPI_FILES = {"openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.json"}

def detect_openapi(root_dir: str) -> dict:
    found = False
    locations = []

    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower() in OPENAPI_FILES:
                found = True
                locations.append(os.path.join(root,f))

    return {
        "compliant": found,
        "evidence": locations if locations else None
    }