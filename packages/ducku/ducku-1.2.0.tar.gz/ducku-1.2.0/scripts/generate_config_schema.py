import os
import yaml
from pydantic import BaseModel
from src.core.configuration import Configuration

def generate_yaml_schema(model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    return schema

def main():
    schema = generate_yaml_schema(Configuration)
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.normpath(os.path.join(here, "..", "config"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ducku_schema.yaml")

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True)

if __name__ == "__main__":
    main()