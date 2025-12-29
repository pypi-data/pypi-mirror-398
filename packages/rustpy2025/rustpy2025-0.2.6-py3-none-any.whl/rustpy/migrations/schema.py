import json, os

SCHEMA_FILE = "rustpy_schema.json"

def load_schema():
    if not os.path.exists(SCHEMA_FILE):
        return {}
    with open(SCHEMA_FILE, "r") as f:
        return json.load(f)

def save_schema(schema):
    with open(SCHEMA_FILE, "w") as f:
        json.dump(schema, f, indent=2)
