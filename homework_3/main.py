import yaml
import argparse
import re
from pathlib import Path

class ConfigTranslator:
    def __init__(self):
        self.constants = {}

    def parse_yaml(self, file_path):
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    #прикол

    def translate_value(self, value):
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, str):
            return f"[[{value}]]"
        elif isinstance(value, dict):
            return self.translate_dict(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

    def translate_dict(self, data):
        items = []
        for key, value in data.items():
            if not re.match(r"^[a-z][a-z0-9_]*$", key):
                raise ValueError(f"Invalid key name: {key}")
            translated_value = self.translate_value(value)
            items.append(f"{key} = {translated_value}")
        return f"dict(\n    " + ",\n    ".join(items) + "\n)"

    def translate(self, data):
        if not isinstance(data, dict):
            raise ValueError("Root element must be a dictionary.")
        result = []
        for key, value in data.items():
            if key.startswith("global "):
                const_name = key.split()[1]
                if not re.match(r"^[a-z][a-z0-9_]*$", const_name):
                    raise ValueError(f"Invalid constant name: {const_name}")
                const_value = self.translate_value(value)
                self.constants[const_name] = const_value
                result.append(f"global {const_name} = {const_value}")
            else:
                translated_value = self.translate_value(value)
                result.append(f"{key} = {translated_value}")
        return "\n".join(result)

def parse_args():
    parser = argparse.ArgumentParser(description="YAML to custom config language translator")
    parser.add_argument("-i", "--input", required=True, help="Path to the input YAML file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output config file")
    return parser.parse_args()

def main():
    args = parse_args()

    translator = ConfigTranslator()
    try:
        data = translator.parse_yaml(args.input)
        translated = translator.translate(data)

        with open(args.output, "w") as out_file:
            out_file.write(translated)

        print(f"Translation successful! Output written to {args.output}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
