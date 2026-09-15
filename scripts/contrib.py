"""assets/contrib.svg — card fixo `git log --graph`: heatmap do último ano + total, streak e recorde."""
from __future__ import annotations

from config import BAR_H, MONTHS_EN, Grid
from github_data import streaks
from heatmap import cells_svg, legend_svg, months_svg, slice_weeks
from svg import Window, fmt_int, span, t


def build_contrib(data: dict, g: Grid, weeks: int) -> str:
    mobile = g.W < 600
    LH, CW, PAD = g.LH, g.CW, g.PAD
    total, current, longest = streaks(data["days"])  # streaks sempre sobre o ano inteiro
    days, ncols = slice_weeks(data["days"], weeks)
    cell, gap = 10, 3
    pitch = cell + gap

    y_prompt = BAR_H + 30
    y_summary = y_prompt + 30
    y_months = y_summary + (30 + LH if mobile else 30)
    y_grid = y_months + 10
    x_grid = PAD + 4 * CW + 6          # espaço para "seg/qua/sex"
    grid_w = ncols * pitch - gap
    assert x_grid + grid_w <= g.W - PAD, f"heatmap não cabe: {x_grid + grid_w:g} > {g.W - PAD}"
    y_legend = y_grid + 7 * pitch + 14
    y_final = y_legend + 38

    w = Window(g, "git", "Terminal: luis@backend — git log --graph (contribuições)")
    w.H = int(y_final + 26)
    a = w.parts.append
    cmd = (f"git log --graph --since={MONTHS_EN[int(days[0]['date'][5:7]) - 1]}" if mobile
           else 'git log --graph --since="1 year ago"')
    t_out = w.typed_prompt(y_prompt, cmd, start=0.45, per_char=0.045)

    line1 = span(fmt_int(total), "bright b") + span(" contribuições no último ano", "text")
    line2 = (span("streak ", "muted") + span(f"{current}d", "green b")
             + span("    recorde ", "muted") + span(f"{longest}d", "yellow b"))
    if mobile:
        a(f'<g class="rise" style="animation-delay:{t_out:.2f}s">{t(PAD, y_summary, line1)}{t(PAD, y_summary + LH, line2)}</g>')
    else:
        a(f'<g class="rise" style="animation-delay:{t_out:.2f}s">{t(PAD, y_summary, line1 + span("    ", "muted") + line2)}</g>')

    a(months_svg(w, days, ncols, x_grid, y_months, pitch, t_out + 0.2))
    a(f'<g class="fade" style="animation-delay:{t_out + 0.2:.2f}s">'
      + "".join(t(PAD, y_grid + r * pitch + cell - 1, span(lbl, "muted small")) for r, lbl in ((1, "seg"), (3, "qua"), (5, "sex")))
      + "</g>")
    cells, t_end = cells_svg(w, days, ncols, x_grid, y_grid, cell, gap, t_out + 0.3, 0.022 if not mobile else 0.04)
    a(cells)
    a(f'<g class="fade" style="animation-delay:{t_end:.2f}s">{legend_svg(x_grid + grid_w, y_legend, cell, CW)}</g>')
    w.final_prompt(y_final, t_end + 0.25)
    return w.close()
