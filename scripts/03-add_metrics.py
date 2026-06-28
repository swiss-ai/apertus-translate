import json
import argparse
from comet import download_model, load_from_checkpoint

args = argparse.ArgumentParser()
args.add_argument("file", type=str)
args = args.parse_args()

with open(args.file, "r") as f:
    data = [json.loads(x) for x in f.readlines()]

METRIC = "COMETKiwi22"
data_missing_metric = set()
for line in data:
    if "scores" not in line:
        line["scores"] = {}
    for model, tgt in line["tgt"].items():
        if METRIC not in line["scores"].get(model, {}):
            data_missing_metric.add((line["src"], tgt))

# limit to 20k so we run it sequentially
data_missing_metric = list(data_missing_metric)[:20_000]
print(len(data_missing_metric), "translations missing metric")

model_path = download_model("Unbabel/wmt22-cometkiwi-da")
model = load_from_checkpoint(model_path)
scores = model.predict(
    [{"src": src, "mt": tgt} for src, tgt in data_missing_metric],
    batch_size=2,
    gpus=1,
).scores # type: ignore

data_missing_metric = {
    (src, tgt): score for (src, tgt), score in zip(data_missing_metric, scores)
}
for line in data:
    for model, tgt in line["tgt"].items():
        if METRIC not in line["scores"].get(model, {}):
            if model not in line["scores"]:
                line["scores"][model] = {}
            if (line["src"], tgt) not in data_missing_metric:
                # print("Missing score for", line["src"], tgt)
                pass
            else:
                line["scores"][model][METRIC] = data_missing_metric[(line["src"], tgt)]

with open(args.file, "w") as f:
    for line in data:
        f.write(json.dumps(line) + "\n")
