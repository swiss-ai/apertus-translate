// typst compile scripts/31-swissgov-table.typ outputs/31-swissgov-table.pdf --root .

#import "@preview/booktabs:0.0.4": *
#show: booktabs-default-table-style
#set page(height: auto, width: auto, margin: 0em)
#set text(font: ("TeX Gyre Pagella", "Palatino"))

#let data = json("../outputs/31-swissgov-table.json")
#let (min, max) = (75, 90)

#let format_cell(x) = {
  let color = if x == none {
    luma(85%)
  } else {
    white.mix(
      (green, calc.max((x - min) / (max - min), 0) * 500%),
      (red, calc.max((max - x) / (max - min), 0) * 500%),
    )
  }
  let body = if x == none {
    []
  } else {
    let s = str(calc.round(x, digits: 1))
    if not s.contains(".") { s += "." }
    let tail = s.split(".").last()
    s + "0" * (1 - tail.len())
  }
  table.cell(inset: 3pt, fill: color, body)
}

#figure(
  table(
    columns: data.directions.len() + 1,
    align: horizon + right,
    toprule(),
    [],
    ..data.directions.map(column => table.cell(
      align: bottom + center,
      stack(
        dir: ltr,
        spacing: 0.3em,
        rotate(-90deg, reflow: true, column.source + [→]),
        rotate(-90deg, reflow: true, column.target),
      ),
    )),
    midrule(),
    ..data.models.enumerate().map(((model_index, model)) => (
      model,
      ..data.directions.map(direction => format_cell(direction.scores.at(model_index))),
    )).flatten(),
    bottomrule(),
  ),
)
