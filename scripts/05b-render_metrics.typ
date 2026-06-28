// typst compile scripts/05b-render_metrics.typ outputs/05b-render_metrics.pdf --root .

#import "@preview/booktabs:0.0.4": *
#show: booktabs-default-table-style
#set page(height: auto, width: auto, margin: 2em)
#set text(font: "TeX Gyre Termes")

#let metrics = json("../outputs/05-metrics.json")

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
  let (min, max) = (0.6, 0.7)
  let color = white.mix(
    (green, calc.max((x - min) / (max - min), 0) * 500%),
    (red, calc.max((max - x) / (max - min), 0) * 500%),
  )
  if model.contains("Apertus") or model.contains("apertus") {
    model = sym.square.filled + " " + model
  } else if "Unbabel-Tower70B".contains(model) {
    model = strike(model)
  }

  let s = str(calc.round(x, digits: 3))
  if not s.contains(".") { s += "." }
  let tail = s.split(".").last()
  (
    table.cell(inset: 3pt, fill: color, text_nowrap(model)),
    table.cell(inset: 3pt, fill: color, s + "0" * (3 - tail.len())),
  )
}

#set align(top)

#{
  stack(
    dir: ltr,
    spacing: 2em,
    ..metrics
      .pairs()
      .filter(((dataset, _)) => not dataset.starts-with("wmt24pp"))
      .map(((dataset, models_scores)) => {
        (
          dataset
            + table(
              columns: 2,
              ..models_scores
                .pairs()
                .map(
                  ((model, score)) => format_cell(model, score),
                )
                .flatten()
            )
        )
      }),
  )
}
