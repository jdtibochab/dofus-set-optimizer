import json
with open('data/MAPPED_ITEMS.json', 'r') as file:
    items = {i["ankama_id"]: i for i in json.load(file)}

with open('data/MAPPED_MOUNTS.json', 'r') as file:
    mounts = {i["ankama_id"]: i for i in json.load(file)}
    for k,v in mounts.items():
        v["type"] = {
            "superTypeId": 99,  # Assign a unique superTypeId for mounts,
            "name" : v["family_name"].copy()
        }
        v["level"] = v.get("level", 60)
        v["conditions"] = v.get("conditions", None)
        
        # Use negative IDs to avoid duplicates
        v["ankama_id"] = -v["ankama_id"]
        items[-k] = v 
        
with open('data/MAPPED_SETS.json', 'r') as file:
    item_sets = {i["ankama_id"]: i for i in json.load(file)}