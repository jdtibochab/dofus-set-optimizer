import json
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

with open(os.path.join(_DATA_DIR, 'MAPPED_ITEMS.json'), 'r') as file:
    items = {i["ankama_id"]: i for i in json.load(file)}
        
with open(os.path.join(_DATA_DIR, 'MAPPED_SETS.json'), 'r') as file:
    item_sets = {i["ankama_id"]: i for i in json.load(file)}
