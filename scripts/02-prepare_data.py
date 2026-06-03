# %%

import subset2evaluate
import json
import requests
import os
import datasets

data = [
    line | {"dataset": f"{k[0]}/{k[1]}"}
    for k, v in subset2evaluate.utils.load_data_wmt_all(
        require_human=False,
        name_filter=lambda k: k[0] in {"wmt25", "wmt24", "wmt24pp"}
    ).items()
    for line in v
]

# download SwissGov data
if not os.path.exists("../data/swissgov_cleaned.json"):
    response = requests.get("https://raw.githubusercontent.com/miwytt/multi-parallel-swissgov/main/swissgov_cleaned.json")
    with open("../data/swissgov_cleaned.json", "w") as f:
        f.write(response.text)
with open("../data/swissgov_cleaned.json", "r") as f:
    data_swissgov = json.load(f)
    data += [
        {
            "src": line[f"text_{lp1}"],
            "tgt": {"human": line[f"text_{lp2}"]},
            "dataset": f"swissgov/{lp1}-{lp2}",
            "doc": line[f"page_en"],
        }
        for line in data_swissgov
        for lp1 in ["de", "it", "fr"]
        for lp2 in ["de", "it", "fr"]
        if lp1 != lp2
    ]

# create custom en->Swiss German data by copying the English side of the WMT25 en-cs data
data_en = [x for x in data if x["dataset"] == "wmt25/en-cs_CZ"]
for lang2 in ["Zürich Swiss German (Züritüütsch)", "Bernese Swiss German (Bärndütsch)", "Eastern Swiss German (St. Gallen, Thurgau)", "Basel Swiss German (Baseldütsch)"]:
    data += [
        {
            "src": line["src"],
            "tgt": {},
            "dataset": f"wmt25custom/en-{lang2}",
            "doc": line["doc"],
        }
        for line in data_en
    ]

# add Romansch data
for lang2, lang2_en in [('rumgr', 'Rumantsch Grischun'), ('sursilv', 'Sursilvan'), ('sutsilv', 'Sutsilvan'), ('surmiran', 'Surmiran'), ('puter', 'Putér'), ('vallader', 'Vallader')]:
    data_rm = datasets.load_dataset("ZurichNLP/wmt24pp-rm", "de_DE-rm-" + lang2, split="test")
    lang2_long = f"Romansh ({lang2_en})"
    data += [
        {
            "src": line["source"],
            "tgt": {"human": line["target"]},
            "dataset": f"wmt24pp/de-{lang2_long}",
            "doc": line["document_id"],
        }
        for line in data_rm
    ]

with open("../data/wmt25_blind.jsonl", "r") as f:
    data_prompt = [json.loads(x) for x in f.readlines()]
    data_prompt = {line["doc_id"]: line["prompt_instruction"] for line in data_prompt}


def langcode_to_long(lang, script=True):
    from babel import Locale

    # babel doesn't know swiss german
    if "Swiss" in lang or "Romansh" in lang:
        return lang

    try:
        if script:
            return Locale.parse(lang, sep="_").get_display_name("en")
        else:
            return Locale.parse(lang, sep="_").get_language_name("en")
    except:
        return Locale.parse(lang.split("_")[0], sep="_").get_language_name("en")


def get_prompt(src, doc, dataset):
    dataset, langs = dataset.split("/")
    if dataset == "wmt25":
        return data_prompt[doc] + "\n\n" + src
    elif dataset in {"wmt24", "wmt24pp", "wmt25custom"}:
        lang1, lang2 = langs.split("-")
        lang1_long = langcode_to_long(lang1, script=False)
        lang2_long = langcode_to_long(lang2, script=True)

        return (
            f"You are a professional {lang1_long} to {lang2_long} translator. Your goal is to accurately convey the meaning and nuances of the original {lang1_long} text while adhering to {lang2_long} grammar, vocabulary, and cultural sensitivities. "
            f"Produce only the {lang2_long} translation, without any additional explanations, commentary, or formatting. "
            f"Please translate the following {lang1_long} text into {lang2_long}:\n\n"
            f"{src}"
        )
    elif dataset in {"swissgov"}:
        lang1, lang2 = langs.split("-")
        lang1_long = langcode_to_long(lang1, script=False)
        lang2_long = langcode_to_long(lang2, script=False)

        return (
            f"You are a professional {lang1_long} to {lang2_long} translator, tasked with providing translations suitable for use in {lang2_long} on government website. "
            f"Produce only the {lang2_long} translation, without any additional explanations, commentary, or formatting. "
            f"Please translate the following {lang1_long} text into {lang2_long}:\n\n"
            f"{src}"
        )
    else:
        raise ValueError(f"Unknown dataset: {dataset}")


print("Starting with ", len(data), "segments")
# filter out canary and unsuitable lines
data = [
    line for line in data
    if "canary" not in line.get("doc", "") and "canary" not in line["src"] and len(line["src"]) > 50
]

data = [
    {"src+prompt": get_prompt(line["src"], line["doc"], line["dataset"])} | line
    for line in data
]
print("Pruned to", len(data), "segments")

language_pairs = {tuple(x["dataset"].split("/")[1].split("-")) for x in data}
print("\n".join([f"{langcode_to_long(lang1, script=False)} -> {langcode_to_long(lang2, script=True)}" for lang1, lang2 in language_pairs]))
print(len(language_pairs), "language pairs")
data_pruned = []
# priority: swissgov, wmt25, wmt24-rm, wmt24pp, wmt24
for lang1, lang2 in language_pairs:
    data_local = [x for x in data if x["dataset"].split("/")[1] == f"{lang1}-{lang2}"]
    # sort by priorities
    data_local.sort(
        key=lambda x: (x["dataset"].startswith("swissgov"), x["dataset"].startswith("wmt25"), x["dataset"].startswith("wmt24pp"), x["dataset"].startswith("wmt24")),
        reverse=True
    )
    data_pruned += data_local[:200]

print("Finalized to ", len(data_pruned), "segments")
with open("../data/all_v2.jsonl", "w") as f:
    for line in data_pruned:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


# %%
import gzip

with open("../data/all_v2.jsonl", "rb") as f:
    with gzip.open("../data/all_v2.jsonl.gz", "wb") as g:
        g.write(f.read())

print("g-zipped")
