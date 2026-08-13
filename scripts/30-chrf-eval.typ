// typst compile scripts/30-chrf-eval.typ outputs/30-chrf-eval.pdf --root .

#import "@preview/booktabs:0.0.4": *
#show: booktabs-default-table-style
#set page(height: auto, width: auto, margin: 0em)
#set text(font: ("TeX Gyre Pagella", "Palatino"))

#let data = json("../outputs/30-chrf-eval.json")
#let (min, max) = (0, 90)
#let panel_size = 26

#let format_cell(x, bold: false) = {
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
    let text = s + "0" * (1 - tail.len())
    if bold { [*#text*] } else { text }
  }
  table.cell(
    inset: 3pt,
    fill: if bold { none } else { color },
    body,
  )
}

#let direction_header(column) = {
  table.cell(
    align: bottom + center,
    stack(
      dir: ltr,
      spacing: 0.3em,
      rotate(-90deg, reflow: true, column.benchmark + "/"),
      rotate(-90deg, reflow: true, column.source + [→] + column.target),
    ),
  )
}

#let chunks(items, size) = {
  let panel_count = calc.max(1, calc.ceil(items.len() / size))
  let base = calc.div-euclid(items.len(), panel_count)
  let remainder = calc.rem(items.len(), panel_count)
  let panels = ()
  let start = 0
  for index in range(panel_count) {
    let stop = start + base + (if index < remainder { 1 } else { 0 })
    panels.push(items.slice(start, stop))
    start = stop
  }
  panels
}

#let averages = range(data.models.len()).map(model_index => {
  let values = data.directions
    .map(direction => direction.scores.at(model_index))
    .filter(x => x != none)
  if values.len() == 0 { none } else { values.sum() / values.len() }
})

#let panels = chunks(data.directions, panel_size)
#let column_count = {
  let widths = panels.map(panel => panel.len())
  widths.at(-1) += 1
  calc.max(..widths)
}

#let heatmap_panel(directions, averages: none) = {
  let show_average = averages != none
  let headers = directions.map(direction_header)
  if show_average {
    headers.push(table.cell(
      align: bottom + center,
      rotate(-90deg, reflow: true, [*Avg.*]),
    ))
  }
  headers += ([],) * (column_count - headers.len())

  let rows = ()
  for (model_index, model) in data.models.enumerate() {
    rows.push(model)
    for direction in directions {
      rows.push(format_cell(direction.scores.at(model_index)))
    }
    if show_average {
      rows.push(format_cell(averages.at(model_index), bold: true))
    }
    rows += ([],) * (column_count - directions.len() - (if show_average { 1 } else { 0 }))
  }

  table(
    columns: column_count + 1,
    align: horizon + right,
    [],
    ..headers,
    midrule(),
    ..rows,
    bottomrule(),
  )
}

#figure(
  stack(
    dir: ttb,
    spacing: 3.5pt,
    ..panels.enumerate().map(((panel_index, panel)) => {
      heatmap_panel(
        panel,
        averages: if panel_index == panels.len() - 1 { averages } else { none },
      )
    }),
  ),
)
