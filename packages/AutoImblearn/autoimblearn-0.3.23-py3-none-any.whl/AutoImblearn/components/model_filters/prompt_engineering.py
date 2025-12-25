import os

api_key_path = os.path.join("../../..", 'data', 'raw', 'openai_key.txt')

with open(api_key_path, 'r') as f:
    api_key = f.readlines()

print(api_key)