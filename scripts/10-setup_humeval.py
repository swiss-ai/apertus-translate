# %%

import json
import random
import os
import fastchrf
import numpy as np

os.makedirs("humeval/campaigns", exist_ok=True)

with open("data/all_v2.jsonl", "r") as f:
# with open("../data/all_v2_apertus.jsonl", "r") as f:
    data = [json.loads(line) for line in f]

MODELS_THAT_WE_WANT = {
    "Ministral-3-8B-Instruct-2512": "Mistral3-8B",
    "Apertus-8B-Instruct-2509": "Apertus1-8B",
    "apertus-v1.5-sft-26-04": "Apertus1.5-8B",
    "utter-project/EuroLLM-22B-Instruct-2512": "EuroLLM-22B",
}

def diversity(tgts: list[str]):
    return -float(np.mean(fastchrf.pairwise_chrf([tgts], [tgts]))) # type: ignore

for languages in {x["languages"] for x in data}:
    lang1, lang2 = languages.split(" -> ")
    data_local = [line for line in data if line["languages"] == languages]
    # we have <400 segments per language pair
    models = {model for line in data_local for model in line["tgt"].keys()}
    # if models:
    #     print(languages, models)

    models = [model for model in MODELS_THAT_WE_WANT.keys() if model in models][:4]
    if not len(models) == 4:
        print("Skipping", languages, "because we don't have 4 models")
        continue

    # take the first 50 that have the highest diversity amongst present models
    r_local = random.Random(0)
    data_local.sort(key=lambda x: r_local.random())
    data_local = data_local[:100]

    data_pearmut = [
        [{
            "src": line["src"].replace("\\n", "\n"),
            "tgt": {MODELS_THAT_WE_WANT[model]: line["tgt"][model].replace("\\n", "\n") for model in models},
            "doc": line["doc"],
        }]
        for line in data_local
    ]

    CAMPAIGN = {
        "info": {
            "assignment": "single-stream",
            "protocol": "cESA",
            "users": 4,
            "shuffle": True,
        },
        "campaign_id": languages,
        # create task-based campaign with duplicate payload and two users
        "data": data_pearmut,
    }
    with open(f"humeval/campaigns/{languages.replace(' -> ', '-')}.json", "w") as f:
        json.dump(CAMPAIGN, f, ensure_ascii=False, indent=2)