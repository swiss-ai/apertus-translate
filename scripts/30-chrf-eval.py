from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sacrebleu.metrics import CHRF

SYSTEM_LABELS = {
    "gemma-4-31B-it": "Gemma 4 31B",
    "gemma-3-12B-it": "Gemma 3 12B",
    "Apertus-8B-Instruct-2509": "Apertus 1.0 8B",
    "human": "Human",
    "apertus-v1.5-sft-26-04": "Apertus 1.5 8B",
    "Ministral-3-8B-Instruct-2512": "Ministral 3 8B",
    "utter-project/EuroLLM-22B-Instruct-2512": "EuroLLM 22B",
}

PINNED_SYSTEMS = frozenset(
    {"Apertus-8B-Instruct-2509", "apertus-v1.5-sft-26-04"}
)

BENCHMARK_LABELS = {
    "wmt24": "WMT24",
    "wmt24pp": "WMT24++",
    "wmt25": "WMT25",
    "wmt25custom": "WMT25 Custom",
}

LANGUAGE_LABELS = {
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bho": "Bhojpuri",
    "bn": "Bengali",
    "ca": "Catalan",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "En.",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "fi": "Finnish",
    "fil": "Filipino",
    "fr": "French",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mas": "Maasai",
    "ml": "Malayalam",
    "mr": "Marathi",
    "nl": "Dutch",
    "no": "Norwegian",
    "pa": "Punjabi",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sr": "Serbian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "zh": "Chinese",
    "zu": "Zulu",
}

TARGET_LABEL_OVERRIDES = {
    "wmt24pp/en-fr_CA": "French (CA)",
    "wmt24pp/en-es_MX": "Spanish (MX)",
    "wmt24pp/en-pt_BR": "Portuguese (BR)",
    "wmt24pp/en-ar_SA": "Arabic (SA)",
    "wmt24pp/en-ar_EG": "Arabic (EG)",
    "wmt24pp/en-sw_KE": "Swahili (KE)",
    "wmt24pp/en-sw_TZ": "Swahili (TZ)",
    "wmt24pp/en-sr_RS": "Serbian (Cyrl.)",
    "wmt24pp/en-zh_CN": "Chinese (Simpl.)",
    "wmt24pp/en-zh_TW": "Chinese (Trad.)",
    "wmt25/en-ar_EG": "Arabic (EG)",
    "wmt25/en-zh_CN": "Chinese (Simpl.)",
    "wmt25/en-sr_Cyrl_RS": "Serbian (Cyrl.)",
    "wmt24pp/de-Romansh (Putér)": "Putér",
    "wmt24pp/de-Romansh (Vallader)": "Vallader",
    "wmt24pp/de-Romansh (Rumantsch Grischun)": "Grischun",
    "wmt24pp/de-Romansh (Sursilvan)": "Sursilvan",
    "wmt24pp/de-Romansh (Surmiran)": "Surmiran",
    "wmt24pp/de-Romansh (Sutsilvan)": "Sutsilvan",
}

MISSING_REFERENCES = frozenset({"", "NaN", "nan", "None", "null"})

SWISS_GERMAN_DATASETS = {
    "wmt25custom/en-Eastern Swiss German (St. Gallen, Thurgau)",
    "wmt25custom/en-Basel Swiss German (Baseldütsch)",
    "wmt25custom/en-Zürich Swiss German (Züritüütsch)",
    "wmt25custom/en-Bernese Swiss German (Bärndütsch)",
}


@dataclass(frozen=True)
class Result:
    benchmark: str
    source: str
    target: str
    scores: tuple[float | None, ...]


def dataset_labels(dataset: str) -> tuple[str, str, str]:
    """Convert a JSONL dataset identifier to the table's display labels."""
    benchmark_key, separator, language_pair = dataset.partition("/")
    if not separator or benchmark_key not in BENCHMARK_LABELS:
        raise ValueError(f"Unsupported dataset identifier: {dataset!r}")

    source_code, separator, target_specifier = language_pair.partition("-")
    if not separator:
        raise ValueError(f"Dataset has no language pair: {dataset!r}")

    try:
        source_label = LANGUAGE_LABELS[source_code]
        target_code = target_specifier.split("_", 1)[0]
        target_label = TARGET_LABEL_OVERRIDES.get(dataset)
        if target_label is None:
            target_label = LANGUAGE_LABELS[target_code]
    except KeyError as error:
        raise ValueError(
            f"Unsupported language code {error.args[0]!r} in {dataset!r}"
        ) from error

    return BENCHMARK_LABELS[benchmark_key], source_label, target_label


def sort_results(labeled_results: list[tuple[str, Result]]) -> list[Result]:
    """Sort directions by descending mean score over the systems that have one."""
    labeled_results.sort(
        key=lambda item: (
            -math.fsum(score for score in item[1].scores if score is not None)
            / sum(score is not None for score in item[1].scores),
            item[0],
        )
    )
    return [result for _, result in labeled_results]


def order_systems(
    systems: Sequence[str], dataset_scores: dict[str, dict[str, float]]
) -> list[str]:
    """Rank systems by descending mean score, keeping the Apertus models on top."""
    collected: dict[str, list[float]] = defaultdict(list)
    for per_system in dataset_scores.values():
        for system, score in per_system.items():
            collected[system].append(score)

    def sort_key(system: str) -> tuple[bool, float, str]:
        scores = collected.get(system)
        mean = -math.inf if not scores else math.fsum(scores) / len(scores)
        return (system not in PINNED_SYSTEMS, -mean, SYSTEM_LABELS[system])

    return sorted(systems, key=sort_key)


def parse_chrf_scores(path: Path) -> tuple[list[str], list[Result]]:
    translations: dict[str, dict[str, tuple[list[str], list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: ([], []))
    )

    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                dataset = record["dataset"]
                targets = record["tgt"]
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid record on line {line_number}: {error}"
                ) from error

            if not isinstance(dataset, str) or not isinstance(targets, dict):
                raise ValueError(
                    f"Line {line_number}: dataset must be a string and tgt an object"
                )
            if dataset.startswith("swissgov/") or dataset in SWISS_GERMAN_DATASETS:
                continue
            if record.get("domain") != "news":
                continue

            reference = targets.get("human")
            if not isinstance(reference, str):
                raise ValueError(
                    f"Line {line_number}: retained dataset {dataset!r} has no human reference"
                )
            if reference.strip() in MISSING_REFERENCES:
                continue

            for system, hypothesis in targets.items():
                if system == "human":
                    continue
                if system not in SYSTEM_LABELS:
                    raise ValueError(
                        f"Line {line_number}: unsupported system {system!r}"
                    )
                if not isinstance(hypothesis, str):
                    raise ValueError(
                        f"Line {line_number}: translation for {system!r} must be a string"
                    )
                hypotheses, references = translations[dataset][system]
                hypotheses.append(hypothesis)
                references.append(reference)

    if not translations:
        raise ValueError(f"No referenced translation records found in {path}")

    systems = [system for system in SYSTEM_LABELS if system != "human"]
    metric = CHRF()
    dataset_scores: dict[str, dict[str, float]] = {}
    dataset_headers: dict[str, tuple[str, str, str]] = {}
    seen_labels: dict[tuple[str, str, str], str] = {}
    for dataset, system_translations in translations.items():
        benchmark, source, target = dataset_labels(dataset)
        display_key = (benchmark, source, target)
        if display_key in seen_labels:
            raise ValueError(
                f"Datasets {seen_labels[display_key]!r} and {dataset!r} both map "
                f"to {benchmark}/{source}→{target}"
            )
        seen_labels[display_key] = dataset
        dataset_headers[dataset] = (benchmark, source, target)

        per_system: dict[str, float] = {}
        for system in systems:
            if system not in system_translations:
                continue
            hypotheses, references = system_translations[system]
            per_system[system] = metric.corpus_score(hypotheses, [references]).score
        dataset_scores[dataset] = per_system

    ordered_systems = order_systems(systems, dataset_scores)
    labeled_results = [
        (
            dataset,
            Result(
                *dataset_headers[dataset],
                tuple(per_system.get(system) for system in ordered_systems),
            ),
        )
        for dataset, per_system in dataset_scores.items()
    ]

    model_names = [SYSTEM_LABELS[system] for system in ordered_systems]
    return model_names, sort_results(labeled_results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="JSONL file containing tgt system outputs and human references",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = Path(__file__).resolve().parent.parent
    json_path = repository_root / "outputs" / "30-chrf-eval.json"
    pdf_path = repository_root / "outputs" / "30-chrf-eval.pdf"

    model_names, results = parse_chrf_scores(args.input)
    payload = {
        "models": list(model_names),
        "directions": [
            {
                "benchmark": result.benchmark,
                "source": result.source,
                "target": result.target,
                "scores": list(result.scores),
            }
            for result in results
        ],
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "typst",
            "compile",
            "scripts/30-chrf-eval.typ",
            str(pdf_path),
            "--root",
            ".",
        ],
        cwd=repository_root,
        check=True,
    )
    print(
        f"Wrote {json_path} and {pdf_path} with {len(results)} ChrF directions "
        f"and {len(model_names)} models."
    )


if __name__ == "__main__":
    main()
