import json
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

with open(os.path.join(_DATA_DIR, 'MAPPED_ITEMS.json'), 'r') as file:
    items = {i["ankama_id"]: i for i in json.load(file)}
        
with open(os.path.join(_DATA_DIR, 'MAPPED_SETS.json'), 'r') as file:
    item_sets = {i["ankama_id"]: i for i in json.load(file)}

if __name__ == "__main__":
    import pandas as pd
    from scripts.utils import get_item_set, elements
    for lang in ['es','en','fr','pt','de']:
        dct = {}
        for k,v in items.items():
            item_set = get_item_set(v,item_sets)
            dct[k] = {
                "name" : v["name"][lang],
                "set" : item_set["name"][lang] if item_set else None,
                "level" : v["level"],
                'ankama_id' : v['ankama_id']
            }
            dct[k].update({i:j for i,j in v['type'].items() if i not in dct[k]})
        Items = pd.DataFrame.from_dict(dct, orient='index').sort_values(
            by=["categoryId", "superTypeId", "itemTypeId"]
            )
        Items.to_csv(f'data/ITEM_NAMES_AND_IDS.{lang}.csv', index=False)
