"""assets/terminal.svg — sessão completa: neofetch → cat stack.txt → cat projetos.txt → git log --graph.

A janela tem a altura do bloco do neofetch (a informação principal aparece sem esperar); os blocos
seguintes entram rolando o conteúdo para cima, como num terminal. Ao terminar, a sessão segura alguns
segundos e recomeça do zero, trazendo o profile de volta ao topo.
"""
from __future__ import annotations

from config import C, FIELDS, LANG_COLORS, MONTHS_EN, PALETTE, PROJECTS, STACK, Grid
from github_data import streaks, top_langs
from heatmap import cells_svg, months_svg, slice_weeks
from svg import LOGO_H, LOGO_W, Session, fmt_int, logo_svg, pack_items, span, t, wrap_text


def _neofetch(s: Session, data: dict, mobile: bool) -> None:
    g = s.g
    LH, CW, PAD = g.LH, g.CW, g.PAD
    s.start_block("neofetch --profile", per_char=0.055)
    y_cmd, t_out, step = s.block_top, s.t, 0.085
    a = s.body.append

    # layout: desktop = logo à esquerda + campos à direita; mobile = logo em cima, campos embaixo
    y_logo_top = y_cmd + 30 - g.FS + 1
    if mobile:
        x_key, y_fields0 = PAD, y_logo_top + LOGO_H + 26
    else:
        x_key, y_fields0 = PAD + LOGO_W + 34, y_cmd + 30
    x_val = x_key + 9 * CW
    a(logo_svg(s, PAD, y_logo_top, t_out))

    a(f'<g {s.anim("rise", t_out + step)}>'
      f'{t(x_key, y_fields0, span("luis", "green b") + span("@", "muted") + span("backend", "blue b"))}</g>')
    a(f'<g {s.anim("rise", t_out + 2 * step)}>{t(x_key, y_fields0 + LH, span("─" * 12, "dim"))}</g>')
    row = 2
    for i, (k, v) in enumerate(FIELDS):  # valor na mesma linha se couber, senão na linha seguinte
        d = t_out + (3 + i) * step
        yk = y_fields0 + LH * row
        if len(v) > g.cols(x_val):
            a(f'<g {s.anim("rise", d)}>{t(x_key, yk, span(k, "blue b"))}{t(x_key + 2 * CW, yk + LH, span(v, "text"))}</g>')
            row += 2
        else:
            a(f'<g {s.anim("rise", d)}>{t(x_key, yk, span(k, "blue b"))}{t(x_val, yk, span(v, "text"))}</g>')
            row += 1
    fields_bottom = y_fields0 + LH * (row - 1)

    # stats ao vivo
    y_stats = max(y_logo_top + LOGO_H, fields_bottom) + 30
    t_stats = t_out + step * (len(FIELDS) + 3) + 0.15
    gap = "  " if mobile else "    "
    stats = (span("repos ", "muted") + span(str(data["repos"]), "bright b")
             + span(f"{gap}stars ", "muted") + span(str(data["stars"]), "yellow b")
             + span(f"{gap}followers ", "muted") + span(str(data["followers"]), "green b")
             + span(f"{gap}since ", "muted") + span(str(data["since"]), "cyan b"))
    a(f'<g {s.anim("rise", t_stats)}>{t(PAD, y_stats, stats)}</g>')

    # barras de linguagem
    langs = top_langs(data["langs"])
    y_bars0, bar_lh = y_stats + 30, LH + 2
    t_bars = t_stats + 0.25
    bar_x = PAD + 12 * CW
    bar_w = min(300, g.W - PAD - bar_x - 7 * CW - 12)
    for i, (name, pct) in enumerate(langs):
        yy, d = y_bars0 + i * bar_lh, t_bars + i * 0.08
        a(f'<g {s.anim("fade", d)}>{t(PAD, yy, span(name, "text"))}'
          f'<rect x="{bar_x:g}" y="{yy - 10}" width="{bar_w:g}" height="10" rx="2" fill="{C["track"]}"/>'
          f'<rect {s.anim("grow", d)} x="{bar_x:g}" y="{yy - 10}" width="{bar_w * pct / 100:.1f}" '
          f'height="10" rx="2" fill="{LANG_COLORS.get(name, C["muted"])}"/>'
          f'{t(bar_x + bar_w + 12, yy, span(f"{pct:5.1f}%", "muted"))}</g>')

    # paleta ANSI
    y_pal = y_bars0 + bar_lh * len(langs) + 12
    t_pal = t_bars + 0.55
    a(f'<g {s.anim("fade", t_pal)}>'
      + "".join(f'<rect x="{PAD + i * 24}" y="{y_pal - 10}" width="20" height="12" rx="2" fill="{c}"/>' for i, c in enumerate(PALETTE))
      + "</g>")
    s.mark(bottom=y_pal + 2, t_end=t_pal + 0.3)
    s.end_block()


def _stack(s: Session) -> None:
    g = s.g
    s.start_block("cat stack.txt")
    x_items = g.PAD + 16 * g.CW
    for label, items in STACK:
        lines = pack_items(items, g.cols(x_items))
        s.line(span(f"{label:<16}", "blue b") + span(lines[0], "text"))
        for cont in lines[1:]:
            s.line(span(cont, "text"), x=x_items)
    s.end_block()


def _projects(s: Session, mobile: bool) -> None:
    """Só nome + stack; a descrição completa fica na tabela fixa do README."""
    g = s.g
    s.start_block("cat projetos.txt")
    if mobile:  # nome numa linha, stack embaixo
        x_stack = g.PAD + 2 * g.CW
        for name, stack in PROJECTS:
            s.line(span(name, "green b"))
            for line in pack_items(stack.split(" · "), g.cols(x_stack)):
                s.line(span(line, "muted"), x=x_stack, step=0.05)
    else:
        x_stack = g.PAD + 26 * g.CW
        for name, stack in PROJECTS:
            lines = pack_items(stack.split(" · "), g.cols(x_stack))
            s.line(span(f"{name:<26}", "green b") + span(lines[0], "text"))
            for cont in lines[1:]:
                s.line(span(cont, "text"), x=x_stack, step=0.05)
    s.end_block()


def _gitlog(s: Session, cdata: dict, weeks: int, mobile: bool) -> None:
    g = s.g
    total, current, longest = streaks(cdata["days"])
    days, ncols = slice_weeks(cdata["days"], weeks)
    cmd = (f"git log --graph --since={MONTHS_EN[int(days[0]['date'][5:7]) - 1]}" if mobile
           else 'git log --graph --since="1 year ago"')
    s.start_block(cmd, per_char=0.045)

    line1 = span(fmt_int(total), "bright b") + span(" contribuições no último ano", "text")
    line2 = (span("streak ", "muted") + span(f"{current}d", "green b")
             + span("    recorde ", "muted") + span(f"{longest}d", "yellow b"))
    if mobile:
        s.line(line1)
        s.line(line2)
    else:
        s.line(line1 + span("    ", "muted") + line2)

    cell, gap = 8, 2
    pitch = cell + gap
    assert g.PAD + ncols * pitch - gap <= g.W - g.PAD, "heatmap não cabe na janela"
    s.y += 6
    s.body.append(months_svg(s, days, ncols, g.PAD, s.y, pitch, s.t))
    y_grid = s.y + 6
    cells, t_end = cells_svg(s, days, ncols, g.PAD, y_grid, cell, gap, s.t + 0.1, 0.02 if not mobile else 0.035)
    s.body.append(cells)
    s.mark(bottom=y_grid + 7 * pitch - gap + 2, t_end=t_end)
    s.end_block()


def build_terminal(tdata: dict, cdata: dict, g: Grid) -> str:
    mobile = g.W < 600
    s = Session(g, "zsh", "Terminal: luis@backend — neofetch --profile, cat stack.txt, cat projetos.txt, git log --graph",
                scroll=True, loop=True, hold=5.0)
    _neofetch(s, tdata, mobile)
    s.H = int(s.bottom + 56)  # a janela mostra o neofetch inteiro; o restante da sessão rola
    _stack(s)
    _projects(s, mobile)
    _gitlog(s, cdata, weeks=26 if mobile else 52, mobile=mobile)
    s.finish()
    return s.close()
