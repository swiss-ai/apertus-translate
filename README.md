# apertus-translate

Evaluating Apertus translation capabilities primarily using human evaluation.

<img width="1000" src="https://github.com/user-attachments/assets/14fc0285-cf04-4d81-9c0a-daa3a9a75a76" />

## Human evaluation

The human evaluation data are in the [release tab](https://github.com/swiss-ai/apertus-translate/releases/tag/humeval), specifically the `annotations.json`, which you can re-analyze:

```bash
wget https://github.com/swiss-ai/apertus-translate/releases/download/humeval/annotations.json -P humeval

# typst is used for rendering
pip install typst
python3 humeval/scripts/20-analyze_humeval.py
typst compile scripts/21-render_humeval.typ outputs/21-render_humeval.pdf --root .
```

To run the human evaluation ([contrastive ESA](https://vilda.net/papers/cesa.pdf)), run:
```bash
pip install fastchrf numpy
python3 scripts/10-setup_humeval.py
cd humeval
pearmut add campaigns/*
pearmut run --port 8001

# you can also make it public if you own ngrok or similar service
pearmut run --port 8001 --url https://pearmut.ngrok.io
ngrok http 8001 --url=pearmut.ngrok.io --traffic-policy-file=policy.yml
```

You can also instead load the annotations in progress into a [Pearmut](https://github.com/zouharvi/pearmut) instance:
```bash
pip install "pearmut>=0.1.6"
wget https://github.com/swiss-ai/apertus-translate/releases/download/humeval/annotations.json
wget https://github.com/swiss-ai/apertus-translate/releases/download/humeval/campaigns.json
wget https://github.com/swiss-ai/apertus-translate/releases/download/humeval/progress.json

pearmut add-existing --campaigns campaigns.json --progress progress.json --annotations annotations.json
```

Or start them from scratch:
```bash
wget https://github.com/swiss-ai/apertus-translate/releases/download/humeval/campaigns.json
pearmut add campaigns.json
```

## Automated evaluation

Running `scripts/02-prepare_data.py` will prepare data for inference in `data/all_v2.jsonl`.
Each line is a dictionary with the following key, among others:
- `src+prompt`: Input to an LLM for translation.
- `tgt`: When you're running inference with model `XYZ`, save the output string to `item["tgt"]["XYZ"]`.

The latest data version (`all_v2.jsonl`) contains WMT*, SwissGov, etc.

Run the following to render a PDF metrics overview.
```bash
# add automated metrics
python3 scripts/03a-add_metrics.py data/all_v2.jsonl
# or just download this file
wget https://github.com/swiss-ai/apertus-translate/releases/download/humeval/all_v2.jsonl
python3 scripts/05a-render_metrics.py data/all_v2.jsonl
typst compile scripts/05b-render_metrics.typ outputs/05b-render_metrics.pdf --root .
```

Additional tables:

```bash
# ChrF scores
pip install sacrebleu
python3 scripts/30-chrf-eval.py data/all_v2.jsonl

# COMETKiwi scores only for SwissGov translation directions
python3 scripts/31-swissgov-table.py data/all_v2.jsonl
```
