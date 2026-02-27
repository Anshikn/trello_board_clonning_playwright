import json
import os

data_path = "data/board_data.json"
if os.path.exists(data_path):
    with open(data_path, 'r') as f:
        data = json.load(f)
        print(json.dumps(data, indent=2))
else:
    print("Data file not found")
