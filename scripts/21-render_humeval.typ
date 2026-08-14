// typst compile scripts/21-render_humeval.typ outputs/21-render_humeval.pdf --root .

#import "@preview/booktabs:0.0.4": *
#show: booktabs-default-table-style
#set page(height: auto, width: auto, margin: 0em)
#set text(font: ("TeX Gyre Pagella", "Palatino"))

#let data = json("../outputs/20-analyze_humeval.json")
#let model_names = (
  "Apertus1-8B": "Apertus 1.0 8B",
  "Apertus1.5-8B": "Apertus 1.5 8B",
  "EuroLLM-22B": "EuroLLM 22B",
  "Mistral3-8B": "Ministral 3 8B",
)
#let models = (
  "Apertus1-8B",
  "Apertus1.5-8B",
  "EuroLLM-22B",
  "Mistral3-8B",
)

// sort data by average score across all models
#let data = data.sorted(
  key: d => -d.model_avg.values().sum() / d.model_avg.len(),
)

#let text_nowrap(x) = {
  box(
    width: 5cm,
    clip: true,
    outset: (y: 3pt),
  )[
    #box(
      width: 1000pt,
      x,
    )
  ]
}

#let format_cell(model, x) = {
  let (min, max) = (0, 90)
  let color = white.mix(
    (green, calc.max((x - min) / (max - min), 0) * 500%),
    (red, calc.max((max - x) / (max - min), 0) * 500%),
  )

  let s = str(calc.round(x, digits: 1))
  if not s.contains(".") { s += "." }
  let tail = s.split(".").last()
  return table.cell(inset: 3pt, fill: color, s + "0" * (1 - tail.len()))
}

#figure(
table(
  columns: data.len()+1,
  align: (horizon+right),
  toprule(),
  [],
  ..data.map(d => {
    let (lang1, lang2) = d.langs.split(" -> ")
    if lang2.contains("(") {
      lang2 = lang2.split("(").at(1).trim(")")
    }
    lang2 = lang2.replace(", Thurgau", "")
    table.cell(
      align: bottom + center,
      stack(
        dir: ltr,
        spacing: 0.3em,
        rotate(-90deg, reflow: true, lang1 + [→]),
        rotate(-90deg, reflow: true, lang2),
      ),
    )
  }),
  midrule(),
  ..models.map(model => (
    model_names.at(model), ..data.map(d => format_cell(model, d.model_avg.at(model))))
  ).flatten(),
  bottomrule(),
),
// caption: [Average human evaluation results for translation.]
)
