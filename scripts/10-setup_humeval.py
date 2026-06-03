# %%

import json
import random
import os

os.makedirs("../humeval/campaigns", exist_ok=True)

with open("../data/all_v2.jsonl", "r") as f:
# with open("../data/all_v2_apertus.jsonl", "r") as f:
    data = [json.loads(line) for line in f]

MODELS_THAT_WE_WANT = ["human"]

for languages in {x["languages"] for x in data}:
    lang1, lang2 = languages.split(" -> ")
    data_local = [line for line in data if line["languages"] == languages]
    # we have <400 segments per language pair
    models = {model for line in data_local for model in line["tgt"].keys()}
    if models:
        print(languages, models)

    models = [model for model in MODELS_THAT_WE_WANT if model in models][:4]
    if not models:
        continue

    # take the first 50 that have the highest diversity amongst present models
    r_local = random.Random(0)
    data_local.sort(key=lambda x: r_local.random())
    data_local = data_local[:50]

    data_pearmut = [
        [{
            "src": line["src"],
            "tgt": {model: line["tgt"][model] for model in models},
            "doc": line["doc"],
        }]
        for line in data_local
    ]

    CAMPAIGN = {
        "info": {
            "assignment": "task-based",
            "protocol": "cESA",
            "users": ["user1", "user2"],
            "shuffle": True,
        },
        "campaign_id": "v1: " + languages,
        # create task-based campaign with duplicate payload and two users
        "data": [data_pearmut]*2,
    }
    with open(f"../humeval/campaigns/{languages.replace(' -> ', '-')}.json", "w") as f:
        json.dump(CAMPAIGN, f, ensure_ascii=False, indent=2)

# %%

data_wrong = [line for line in data if not isinstance(line, dict)]
print(data_wrong[0])