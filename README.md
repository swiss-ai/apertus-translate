# apertus-translate
Experiments with making Apertus translate and other multilingual tasks


## Data description

Running `scripts/02-prepare_data.py` will prepare data for inference in `data/all_v2.jsonl`.
Each line is a dictionary with the following key, among others:
- `src+prompt`: Input to an LLM for translation.
- `tgt`: When you're running inference with model `XYZ`, save the output string to `item["tgt"]["XYZ"]`.

Data versions:
- `all_v2.jsonl` contains WMT*, SwissGov, etc.
- `all_v1.jsonl` contains WMT24, WMT24++ and WMT25, including parts without human evaluation
- `all_v0.jsonl` contains WMT24++ and WMT25, including parts without human evaluation

## Scripts

Run the following to render the PDF metrics overview. You'll need Typst amongst the typical software stack:
```bash
python3 scripts/03a-add_metrics.py data/all_v2.jsonl
python3 scripts/05a-render_metrics.py data/all_v2.jsonl
typst compile scripts/05b-render_metrics.typ outputs/05b-render_metrics.pdf --root .
```

To run the human evaluation (v2), run:
```bash
python3 scripts/10-setup_humeval.py
cd humeval
pearmut add campaigns/*
pearmut run --port 8001 --url https://pearmut.ngrok.io
ngrok http 8001 --url=pearmut.ngrok.io --traffic-policy-file=policy.yml
```