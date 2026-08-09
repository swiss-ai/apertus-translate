// typst compile scripts/05b-render_metrics.typ outputs/translation_autoeval.pdf --root .

#import "@preview/booktabs:0.0.4": *
#show: booktabs-default-table-style
#set page(height: auto, width: auto, margin: 0em)
#set text(font: "TeX Gyre Termes")

#let data = json("../outputs/05-analyze_metrics.json")
#let models = data.at(0).model_avg.keys()

// sort models by average score across all languages
#let models = models.sorted(
  key: a => {
    let nonzero = data.filter(d => d.model_avg.keys().contains(a))
    -nonzero.map(d => d.model_avg.at(a)).sum() / nonzero.len()
  },
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
  if x == 0 { return table.cell(inset: 3pt, fill: luma(200))[] }
  x = x * 100
  let (min, max) = (50, 90)
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

#let CHUNKS = 4
#let CHUNK_LEN = calc.ceil(data.len() / CHUNKS)

#for c in range(0, CHUNKS) {
  let data_local = data.slice(c * CHUNK_LEN, calc.min((c + 1) * CHUNK_LEN, data.len()))
  table(
    columns: data_local.len()+1,
    align: (bottom+right),
    // toprule(),
    [],
    ..data_local.map(d => {
      let (lang1, lang2) = d.langs.replace("English", "En.").replace("Rumantsch Grischun", "Grischun").split(" -> ")
      if lang2.contains("(") {
        lang2 = lang2.split("(").at(1).trim(")").replace(", Thurgau", "")
      }
      let dataset = d.dataset
      return align(left+bottom, rotate(-90deg, reflow: true, dataset + "/ " + v(-10pt) + lang1 + sym.arrow + lang2))
    }),
    midrule(),
    ..models.map(model => (
      model, ..data_local.map(d => format_cell(model, d.model_avg.at(model, default: 0))))
    ).flatten(),
    bottomrule(),
  )+h(1fr)+v(-50pt)
  linebreak()
}
#v(20pt)