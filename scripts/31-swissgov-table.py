from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

COMETKIWI_METRIC = "COMETKiwi22"

SYSTEM_LABELS = {
    "gemma-4-31B-it": "Gemma 4 31B",
    "gemma-3-12B-it": "Gemma 3 12B",
    "Apertus-8B-Instruct-2509": "Apertus 1.0 8B",
    "human": "Human",
    "apertus-v1.5-sft-26-04": "Apertus 1.5 8B",
    "Ministral-3-8B-Instruct-2512": "Ministral 3 8B",
    "utter-project/EuroLLM-22B-Instruct-2512": "EuroLLM 22B",
}

SYSTEM_ROW_ORDER = [
    "Apertus-8B-Instruct-2509",
    "apertus-v1.5-sft-26-04",
    "gemma-4-31B-it",
    "gemma-3-12B-it",
    "utter-project/EuroLLM-22B-Instruct-2512",
    "Ministral-3-8B-Instruct-2512",
]

LANGUAGE_LABELS = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "it": "Italian",
}


@dataclass(frozen=True)
class Result:
    source: str
    target: str
    scores: tuple[float | None, ...]


def dataset_labels(dataset: str) -> tuple[str, str]:
    prefix, separator, language_pair = dataset.partition("/")
    if prefix != "swissgov" or not separator:
        raise ValueError(f"Unsupported dataset identifier: {dataset!r}")

    source_code, separator, target_code = language_pair.partition("-")
    if not separator:
        raise ValueError(f"Dataset has no language pair: {dataset!r}")

    try:
        return LANGUAGE_LABELS[source_code], LANGUAGE_LABELS[target_code]
    except KeyError as error:
        raise ValueError(
            f"Unsupported language code {error.args[0]!r} in {dataset!r}"
        ) from error


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


def parse_cometkiwi_scores(path: Path) -> tuple[list[str], list[Result]]:
    grouped_scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                dataset = record["dataset"]
                scores_by_system = record["scores"]
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid record on line {line_number}: {error}"
                ) from error

            if not isinstance(dataset, str) or not isinstance(scores_by_system, dict):
                raise ValueError(
                    f"Line {line_number}: dataset must be a string and scores an object"
                )
            if not dataset.startswith("swissgov/"):
                continue

            for system, metric_scores in scores_by_system.items():
                if not isinstance(system, str):
                    raise ValueError(f"Line {line_number}: system keys must be strings")
                if system not in SYSTEM_LABELS:
                    raise ValueError(
                        f"Line {line_number}: unsupported system {system!r}"
                    )
                if not isinstance(metric_scores, dict):
                    raise ValueError(
                        f"Line {line_number}: scores for {system!r} must be an object"
                    )
                try:
                    score = float(metric_scores[COMETKIWI_METRIC])
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(
                        f"Line {line_number}: {system!r} is missing a finite "
                        f"{COMETKIWI_METRIC} score"
                    ) from error
                if not math.isfinite(score):
                    raise ValueError(
                        f"Line {line_number}: {system!r} {COMETKIWI_METRIC} "
                        "score must be finite"
                    )
                grouped_scores[dataset][system].append(score)

    if not grouped_scores:
        raise ValueError(f"No SwissGov JSONL records found in {path}")

    scored_systems = {
        system for by_system in grouped_scores.values() for system in by_system
    }
    systems = [
        system
        for system in list(SYSTEM_ROW_ORDER)
        + [system for system in SYSTEM_LABELS if system not in SYSTEM_ROW_ORDER]
        if system in scored_systems
    ]
    model_names = [SYSTEM_LABELS[system] for system in systems]
    labeled_results: list[tuple[str, Result]] = []
    seen_labels: dict[tuple[str, str], str] = {}
    for dataset, system_scores in grouped_scores.items():
        source, target = dataset_labels(dataset)
        display_key = (source, target)
        if display_key in seen_labels:
            raise ValueError(
                f"Datasets {seen_labels[display_key]!r} and {dataset!r} both map "
                f"to {source}→{target}"
            )
        seen_labels[display_key] = dataset

        scores = tuple(
            100.0 * math.fsum(system_scores[system]) / len(system_scores[system])
            if system in system_scores
            else None
            for system in systems
        )
        labeled_results.append((dataset, Result(source, target, scores)))

    return model_names, sort_results(labeled_results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="JSONL file containing per-system COMETKiwi scores",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = Path(__file__).resolve().parent.parent
    json_path = repository_root / "outputs" / "31-swissgov-table.json"
    pdf_path = repository_root / "outputs" / "31-swissgov-table.pdf"

    model_names, results = parse_cometkiwi_scores(args.input)
    payload = {
        "models": list(model_names),
        "directions": [
            {
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
            "scripts/31-swissgov-table.typ",
            str(pdf_path),
            "--root",
            ".",
        ],
        cwd=repository_root,
        check=True,
    )
    print(
        f"Wrote {json_path} and {pdf_path} with {len(results)} SwissGov "
        f"COMETKiwi directions and {len(model_names)} models."
    )


if __name__ == "__main__":
    main()
