"""Heatmap de contribuições (grade 7 linhas × N semanas) usado no hero e no card `git log --graph`."""
from __future__ import annotations

from config import C, HEAT, MONTHS_PT
from svg import Window, span, t


def slice_weeks(days: list[dict], weeks: int | None) -> tuple[list[dict], int]:
    """Mantém só as últimas `weeks` colunas (reindexadas a partir de 0). Retorna (dias, nº de colunas)."""
    ncols_all = max(d["col"] for d in days) + 1
    first = max(0, ncols_all - weeks) if weeks else 0
    sliced = [dict(d, col=d["col"] - first) for d in days if d["col"] >= first]
    return sliced, ncols_all - first


def month_label_cols(days: list[dict], ncols: int) -> list[tuple[int, int]]:
    """(coluna, mês) onde o mês muda; descarta o rótulo da 1ª coluna se colidir com o seguinte."""
    first_by_col: dict[int, str] = {}
    for d in days:
        if d["col"] not in first_by_col or d["date"] < first_by_col[d["col"]]:
            first_by_col[d["col"]] = d["date"]
    labels: list[tuple[int, int]] = []
    prev = None
    for col in range(ncols):
        m = int(first_by_col.get(col, "0000-01-01")[5:7])
        if (prev is None or m != prev) and col <= ncols - 2:
            labels.append((col, m))
        prev = m
    if len(labels) >= 2 and labels[1][0] - labels[0][0] < 3:
        labels.pop(0)
    return labels


def months_svg(w: Window, days: list[dict], ncols: int, x0: float, y: float, pitch: float, start: float) -> str:
    labels = "".join(t(x0 + col * pitch, y, span(MONTHS_PT[m - 1], "muted small"))
                     for col, m in month_label_cols(days, ncols))
    return f'<g {w.anim("fade", start)}>{labels}</g>'


def cells_svg(w: Window, days: list[dict], ncols: int, x0: float, y0: float, cell: float, gap: float,
              start: float, per_col: float) -> tuple[str, float]:
    """Células reveladas coluna a coluna. Nível 0 ganha contorno sutil para a grade ficar legível.
    Retorna (svg, instante em que a última coluna aparece)."""
    pitch = cell + gap
    by_col: dict[int, list[dict]] = {}
    for d in days:
        by_col.setdefault(d["col"], []).append(d)
    out = []
    for col in range(ncols):
        cells = "".join(
            f'<rect x="{x0 + col * pitch:g}" y="{y0 + d["row"] * pitch:g}" width="{cell:g}" height="{cell:g}" rx="2" '
            f'fill="{HEAT[min(d["level"], 4)]}"'
            + (f' stroke="{C["border"]}" stroke-opacity=".55"' if d["level"] == 0 else "") + "/>"
            for d in by_col.get(col, []))
        out.append(f'<g {w.anim("rise", start + col * per_col)}>{cells}</g>')
    return "".join(out), start + ncols * per_col + 0.3


def legend_svg(x_right: float, y: float, cell: float, cw: float) -> str:
    lx = x_right - 5 * (cell + 3) - 4 * cw - 8
    svg = t(lx - 6 * cw, y + cell - 1, span("menos", "muted small"), "", ' text-anchor="end"')
    svg += "".join(f'<rect x="{lx + i * (cell + 3):g}" y="{y:g}" width="{cell:g}" height="{cell:g}" rx="2" fill="{c}"/>'
                   for i, c in enumerate(HEAT))
    svg += t(lx + 5 * (cell + 3) + 4, y + cell - 1, span("mais", "muted small"))
    return svg
