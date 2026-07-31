// typst compile scripts/21-render_humeval.typ outputs/21-render_humeval.pdf --root .

#import "@preview/booktabs:0.0.4": *
#show: booktabs-default-table-style
#set page(height: auto, width: auto, margin: 0em)
#set text(font: "TeX Gyre Termes")

#let data = json("../outputs/20-analyze_humeval.json")
#let models = data.at(0).model_avg.keys()

// sort models by average score across all languages
#let models = models.sorted(
  key: a => -data.map(d => d.model_avg.at(a)).sum() / data.len(),
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

#set align(top)

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
    return align(left+bottom, rotate(-70deg, reflow: true, stack(spacing: 0.3em, lang1 + sym.arrow, lang2)))
  }),
  midrule(),
  ..models.map(model => (
    model, ..data.map(d => format_cell(model, d.model_avg.at(model))))
  ).flatten(),
  bottomrule(),
),
// caption: [Average human evaluation results for translation.]
)
