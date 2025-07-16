# In your root folder (internship_task/)
import json
import yaml

with open('inventory_openapi.json', 'r') as json_file:
    json_data = json.load(json_file)

with open('openapi.yaml', 'w') as yaml_file:
    yaml.dump(json_data, yaml_file, sort_keys=False, indent=2)

print("openapi.json converted to openapi.yaml in root directory.")