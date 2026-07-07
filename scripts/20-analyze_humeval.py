# %%

import os
import json
import statistics
os.chdir(os.path.dirname(__file__) + "/..")

data_out = []

with open("humeval/annotations.json", "r") as f:
    for campaign_name, data in json.load(f).items():
        data_local = [
            ann
            for item in data
            for ann in item["annotation"]
        ]

        if not data_local:
            continue

        # model averages
        models = data_local[0].keys()
        model_avg = {
            model: statistics.mean([item[model]["score"] for item in data_local]) for model in models
        }

        data_out.append({"langs": campaign_name, "model_avg": model_avg})

with open("outputs/20-analyze_humeval.json", "w") as f:
    json.dump(data_out, f, indent=2, ensure_ascii=False)