"""Primitivas SVG, janela de terminal (Window) e sessão com rolagem/loop (Session).

Toda animação é CSS @keyframes dentro do <style> do SVG — é o que o GitHub executa ao renderizar
o arquivo via <img>. Fonte embutida em base64; nenhum recurso externo.

Dois modos de animar um elemento (`Window.anim`):
  - one-shot (Window / contrib.svg): classe `rise|fade|bar` + `animation-delay`; roda uma vez.
  - loop (Session com loop=True): cada elemento ganha keyframes próprios em % de um ciclo comum `T`,
    com `infinite`; ao fim do ciclo tudo volta ao estado inicial (a sessão recomeça do zero).
"""
from __future__ import annotations

import base64
from html import escape

from config import BAR_H, C, FONT_PATH, LOGO, LOGO_CELL_H, LOGO_CELL_W, PROMPT_STR, Grid

_H, _HS, _HB, _T = "__H__", "__HS__", "__HB__", "__T__"  # placeholders resolvidos em close()

# kind: (estado inicial, estado final, duração padrão, easing)
ANIMS = {
    "rise": ("opacity:0;transform:translateY(6px)", "opacity:1;transform:translateY(0)", 0.32, "cubic-bezier(.2,.7,.2,1)"),
    "fade": ("opacity:0", "opacity:1", 0.4, "ease"),
    "grow": ("transform:scaleX(0)", "transform:scaleX(1)", 0.55, "cubic-bezier(.2,.7,.2,1)"),
}
_CLASS = {"rise": "rise", "fade": "fade", "grow": "bar"}


# ---------------------------------------------------------------- texto
def t(x: float, y: float, content: str, cls: str = "", extra: str = "") -> str:
    cls_attr = f' class="{cls}"' if cls else ""
    return f'<text x="{x:g}" y="{y:g}"{cls_attr} xml:space="preserve"{extra}>{content}</text>'


def span(content: str, cls: str) -> str:
    return f'<tspan class="{cls}">{escape(content)}</tspan>'


def prompt() -> str:
    return (span("luis", "green b") + span("@", "muted") + span("backend", "blue b")
            + span(":", "text") + span("~", "cyan") + span("$ ", "text"))


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def wrap_text(text: str, cols: int) -> list[str]:
    """Quebra por palavras para caber em `cols` caracteres."""
    lines: list[str] = []
    cur = ""
    for word in text.split(" "):
        cand = word if not cur else f"{cur} {word}"
        if len(cand) <= cols or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def pack_items(items: list[str], cols: int, sep: str = " · ") -> list[str]:
    """Junta itens com `sep` quebrando em `cols`; o separador fica no fim da linha, nunca no início."""
    lines: list[str] = []
    cur = ""
    for i, item in enumerate(items):
        tail = sep.rstrip() if i < len(items) - 1 else ""
        cand = item if not cur else f"{cur} {item}"
        if len(cand + tail) <= cols or not cur:
            cur = cand + tail
        else:
            lines.append(cur)
            cur = item + tail
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- logo pixel-art
def logo_rects(x0: float, y0: float, cw: float, ch: float) -> list[tuple[float, float, float, float]]:
    rects = []
    for r, row in enumerate(LOGO):
        c = 0
        while c < len(row):
            if row[c] == "█":
                start = c
                while c < len(row) and row[c] == "█":
                    c += 1
                rects.append((x0 + start * cw, y0 + r * ch, (c - start) * cw, ch))
            else:
                c += 1
    return rects


def logo_svg(w: "Window", x: float, y: float, start: float) -> str:
    rects = logo_rects(x, y, LOGO_CELL_W, LOGO_CELL_H)
    body = "".join(f'<rect x="{rx:g}" y="{ry:g}" width="{rw:g}" height="{rh:g}"/>' for rx, ry, rw, rh in rects)
    return (f'<g {w.anim("rise", start)}>'
            f'<g fill="{C["green_dim"]}" fill-opacity=".9" transform="translate(4 4)">{body}</g>'
            f'<g fill="{C["green"]}" filter="url(#glow)">{body}</g></g>')


LOGO_W = len(LOGO[0]) * LOGO_CELL_W
LOGO_H = len(LOGO) * LOGO_CELL_H + 4


# ---------------------------------------------------------------- janela
class Window:
    """Janela de terminal: defs (fonte, keyframes, overlays CRT), barra de título, prompts."""

    def __init__(self, g: Grid, process: str, label: str) -> None:
        self.g = g
        self.H: int | None = None
        self.T: float | None = None          # duração do ciclo (só no modo loop)
        self.loop = False
        self.parts: list[str] = []
        self.body: list[str] = []            # conteúdo rolável (usado pela Session)
        self.out = self.parts                # onde os prompts são escritos
        self._n = 0                          # contador de animações/keyframes
        self._pending: list[tuple] = []      # animações do modo loop, geradas quando T é conhecido
        title = f"luis@backend: ~ — {process}"
        font_b64 = base64.b64encode(FONT_PATH.read_bytes()).decode("ascii")
        a = self.parts.append
        a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {g.W} {_H}" width="{g.W}" height="{_H}" '
          f'role="img" aria-label="{escape(label)}">')
        a(f"<title>{escape(label)}</title>")
        a("<defs><style>")
        a(f'@font-face{{font-family:"JBM";font-weight:100 800;font-display:block;'
          f'src:url(data:font/woff2;base64,{font_b64}) format("woff2");}}')
        a(f'text{{font-family:"JBM","JetBrains Mono","Cascadia Code","Fira Code",Consolas,monospace;'
          f'font-size:{g.FS:g}px;fill:{C["text"]};}}')
        a(f'.b{{font-weight:700}}.text{{fill:{C["text"]}}}.bright{{fill:{C["bright"]}}}.muted{{fill:{C["muted"]}}}'
          f'.dim{{fill:{C["dim"]}}}.green{{fill:{C["green"]}}}.blue{{fill:{C["blue"]}}}.cyan{{fill:{C["cyan"]}}}'
          f'.yellow{{fill:{C["yellow"]}}}.title{{fill:{C["muted"]};font-size:{g.FS - 1.5:g}px}}'
          f'.small{{font-size:{g.FS - 2:g}px}}')
        a("@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}")
        a("@keyframes fade{from{opacity:0}to{opacity:1}}")
        a("@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}")
        a("@keyframes blink{50%{opacity:0}}")
        a(f"@keyframes sweep{{from{{transform:translateY(-80px)}}to{{transform:translateY({_HS}px)}}}}")
        a("@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}")
        a(".rise{opacity:0;animation:rise .32s cubic-bezier(.2,.7,.2,1) both}")
        a(".fade{opacity:0;animation:fade .4s ease both}")
        a(".bar{transform-box:fill-box;transform-origin:left center;transform:scaleX(0);"
          "animation:grow .55s cubic-bezier(.2,.7,.2,1) both}")
        a(".cursor{animation:blink 1.05s steps(1,end) infinite}")
        a(".sweep{animation:sweep 9s linear infinite;animation-delay:2s}")
        a("@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;animation-delay:0s!important;"
          "animation-iteration-count:1!important}.sweep{display:none}}")
        self.style_extra_index = len(self.parts)  # regras extras entram aqui
        a("</style>")
        a('<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
          '<rect width="4" height="1.2" fill="#000" fill-opacity=".16"/></pattern>')
        a('<linearGradient id="sweepGrad" x1="0" y1="0" x2="0" y2="1">'
          '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".035"/>'
          '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
        a('<filter id="glow" x="-10%" y="-20%" width="120%" height="140%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
          '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
        a(f'<clipPath id="win"><rect width="{g.W}" height="{_H}" rx="10"/></clipPath>')
        a(f'<clipPath id="body"><rect y="{BAR_H + 1}" width="{g.W}" height="{_HB}"/></clipPath>')
        a("</defs>")
        a('<g clip-path="url(#win)">')
        a(f'<rect width="{g.W}" height="{_H}" rx="10" fill="{C["canvas"]}"/>')
        a(f'<rect width="{g.W}" height="{BAR_H}" fill="{C["surface"]}"/>')
        a(f'<line x1="0" y1="{BAR_H}.5" x2="{g.W}" y2="{BAR_H}.5" stroke="{C["border"]}"/>')
        for i, col in enumerate((C["tl_red"], C["tl_yellow"], C["tl_green"])):
            a(f'<circle cx="{20 + i * 18}" cy="{BAR_H / 2:g}" r="5.5" fill="{col}"/>')
        a(t(g.W / 2, BAR_H / 2 + 4, escape(title), "title", ' text-anchor="middle"'))

    # ------------------------------------------------------------ animações
    def add_style(self, css: str) -> None:
        self.parts.insert(self.style_extra_index, css)
        self.style_extra_index += 1

    def _pct(self, s: float) -> str:
        assert self.T
        return f"{max(0.0, 100 * s / self.T):.3f}%"

    def anim(self, kind: str, start: float, dur: float | None = None) -> str:
        """Atributos (class/style) que animam um elemento a partir do instante `start`."""
        frm, to, d0, ease = ANIMS[kind]
        dur = d0 if dur is None else dur
        if not self.loop:
            return f'class="{_CLASS[kind]}" style="animation-delay:{start:.2f}s"'
        self._n += 1
        n = self._n
        self._pending.append(("anim", n, frm, to, start, dur, ease))
        extra = "transform-box:fill-box;transform-origin:left center;" if kind == "grow" else ""
        return f'style="{extra}animation:a{n} {_T}s linear infinite"'

    def typed_prompt(self, y: float, cmd: str, start: float, per_char: float = 0.05, appear: bool = False) -> float:
        """Prompt + comando digitado com caret. Retorna o instante em que a saída pode começar."""
        g = self.g
        assert len(PROMPT_STR) + len(cmd) <= g.cols(g.PAD), f"comando não cabe na largura {g.W}: {cmd!r}"
        self._n += 1
        n = self._n
        dur = per_char * len(cmd)
        end = start + dur
        cmd_x = g.PAD + len(PROMPT_STR) * g.CW
        shift = len(cmd) * g.CW
        if self.loop:
            self._pending.append(("typed", n, cmd, start, end, shift, appear))
        else:
            total = end + 0.35
            p1 = max(0.0, (start - 0.05) / total * 100) if appear else 0.0
            self.add_style(
                f"@keyframes caret{n}{{from{{transform:translateX(0)}}to{{transform:translateX({shift:g}px)}}}}"
                f"@keyframes vis{n}{{0%,{p1:.3f}%{{visibility:hidden}}{p1 + 0.001:.3f}%,99.99%{{visibility:visible}}100%{{visibility:hidden}}}}"
                f".cmd{n}{{clip-path:inset(0 100% 0 0);animation:type {dur:.3f}s steps({len(cmd)},end) {start:.2f}s both}}"
                f".caret{n}{{animation:caret{n} {dur:.3f}s steps({len(cmd)},end) {start:.2f}s both,"
                f"blink 1s steps(1,end) infinite,vis{n} {total:.2f}s linear both}}")
        a = self.out.append
        line = t(g.PAD, y, prompt())
        a(f'<g {self.anim("fade", start - 0.05, 0.01)}>{line}</g>' if appear else line)
        a(f'<g class="cmd{n}">{t(cmd_x, y, span(cmd, "bright"))}</g>')
        a(f'<rect class="caret{n}" x="{cmd_x:g}" y="{y - g.FS + 1:g}" width="{g.CW:g}" height="{g.FS + 3:g}" fill="{C["green"]}"/>')
        return end + 0.35

    def final_prompt(self, y: float, at: float) -> None:
        g = self.g
        cmd_x = g.PAD + len(PROMPT_STR) * g.CW
        self.out.append(
            f'<g {self.anim("fade", at)}>{t(g.PAD, y, prompt())}'
            f'<rect class="cursor" x="{cmd_x:g}" y="{y - g.FS + 1:g}" width="{g.CW:g}" height="{g.FS + 3:g}" fill="{C["green"]}"/></g>')

    def _flush_loop_css(self) -> None:
        """Gera os keyframes do modo loop (precisa de T definido)."""
        assert self.T
        P = self._pct
        for item in self._pending:
            if item[0] == "anim":
                _, n, frm, to, start, dur, ease = item
                self.add_style(f"@keyframes a{n}{{0%,{P(start)}{{{frm};animation-timing-function:{ease}}}"
                               f"{P(start + dur)},100%{{{to}}}}}")
            else:
                _, n, cmd, start, end, shift, appear = item
                steps = f"steps({len(cmd)},end)"
                v0 = P(start - 0.05) if appear else "0%"
                self.add_style(
                    f"@keyframes type{n}{{0%,{P(start)}{{clip-path:inset(0 100% 0 0);animation-timing-function:{steps}}}"
                    f"{P(end)},100%{{clip-path:inset(0 0 0 0)}}}}"
                    f"@keyframes caret{n}{{0%,{P(start)}{{transform:translateX(0);animation-timing-function:{steps}}}"
                    f"{P(end)},100%{{transform:translateX({shift:g}px)}}}}"
                    f"@keyframes vis{n}{{0%,{v0}{{visibility:hidden}}{P(start - 0.049)},{P(end + 0.35)}{{visibility:visible}}"
                    f"{P(end + 0.351)},100%{{visibility:hidden}}}}"
                    f".cmd{n}{{animation:type{n} {_T}s linear infinite}}"
                    f".caret{n}{{animation:caret{n} {_T}s linear infinite,blink 1s steps(1,end) infinite,vis{n} {_T}s linear infinite}}")
        self._pending.clear()

    def close(self) -> str:
        assert self.H, "defina window.H antes de fechar"
        g, a = self.g, self.parts.append
        if self.body:
            a('<g clip-path="url(#body)"><g class="scroll">')
            a("\n".join(self.body))
            a("</g></g>")
        a(f'<rect class="sweep" x="0" y="0" width="{g.W}" height="80" fill="url(#sweepGrad)"/>')
        a(f'<rect x="0" y="{BAR_H + 1}" width="{g.W}" height="{self.H - BAR_H - 1}" fill="url(#scan)"/>')
        a("</g>")
        a(f'<rect x=".5" y=".5" width="{g.W - 1}" height="{self.H - 1}" rx="10" fill="none" stroke="{C["border"]}"/>')
        a("</svg>")
        svg = "\n".join(self.parts) + "\n"
        svg = svg.replace(_HS, str(self.H + 80)).replace(_HB, str(self.H - BAR_H - 1)).replace(_H, str(self.H))
        if self.T:
            svg = svg.replace(_T, f"{self.T:.2f}")
        return svg


# ---------------------------------------------------------------- sessão
class Session(Window):
    """Vários comandos em sequência numa janela de altura fixa.

    scroll: quando a saída não cabe, o conteúdo rola para cima como num terminal.
    loop:   ao terminar, segura `hold` segundos e recomeça do zero (o profile volta ao topo).
    Convenções: `y` é a linha de base da próxima linha; `t` o instante da próxima animação;
    `bottom` a borda inferior do que já foi desenhado.
    """

    def __init__(self, g: Grid, process: str, label: str, scroll: bool = True,
                 loop: bool = True, hold: float = 5.0) -> None:
        super().__init__(g, process, label)
        self.scroll = scroll
        self.loop = loop
        self.hold = hold
        self.out = self.body
        self.y: float = BAR_H + 30
        self.t: float = 0.45
        self.bottom: float = self.y
        self.offset: float = 0.0
        self.events: list[tuple[float, float]] = []
        self.first = True
        self.block_top = self.y
        self.block_tcmd = self.t
        self.t_end = 0.0

    def start_block(self, cmd: str, per_char: float = 0.055, pause: float = 1.0) -> None:
        if not self.first:
            self.y = self.bottom + 34
            self.t += pause
        self.block_top, self.block_tcmd = self.y, self.t
        self.t = self.typed_prompt(self.y, cmd, start=self.t, per_char=per_char, appear=not self.first)
        self.first = False
        self.bottom = self.y + 4
        self.y += self.g.LH + 8   # primeira linha de saída

    def line(self, html: str, x: float | None = None, step: float = 0.085) -> None:
        g = self.g
        self.body.append(f'<g {self.anim("rise", self.t)}>{t(g.PAD if x is None else x, self.y, html)}</g>')
        self.bottom = max(self.bottom, self.y + 4)
        self.y += g.LH
        self.t += step

    def mark(self, bottom: float, t_end: float) -> None:
        """Registra a borda inferior e o fim da animação de um bloco desenhado manualmente."""
        self.bottom = max(self.bottom, bottom)
        self.y = max(self.y, bottom + self.g.LH)
        self.t = max(self.t, t_end)

    def end_block(self) -> None:
        self._scroll_to(self.bottom, self.block_tcmd)

    def _scroll_to(self, bottom: float, at: float) -> None:
        if not self.scroll or self.H is None:
            return
        need = bottom + 16 - self.H
        if need > self.offset + 0.5:
            assert self.block_top - need >= BAR_H + 20, "bloco maior que a janela visível"
            self.events += [(at - 0.55, self.offset), (at - 0.1, need)]
            self.offset = need

    def finish(self) -> None:
        y = self.bottom + 34
        at = self.t + 0.6
        self.block_top = y
        self._scroll_to(y + 6, at)
        self.final_prompt(y, at)
        self.t_end = at + 1.0
        if self.H is None:              # sem rolagem: a janela abraça toda a sessão
            self.H = int(y + 26)
        total = self.t_end + (self.hold if self.loop else 0.0)
        if self.loop:
            self.T = total
            self._flush_loop_css()
        if not self.events:
            return
        iters = "infinite" if self.loop else "both"
        kf = ["0%{transform:translateY(0)}"]
        for i in range(0, len(self.events), 2):
            (ts, o0), (te, o1) = self.events[i], self.events[i + 1]
            kf.append(f"{100 * ts / total:.3f}%{{transform:translateY({-o0:g}px);animation-timing-function:cubic-bezier(.2,.7,.2,1)}}")
            kf.append(f"{100 * te / total:.3f}%{{transform:translateY({-o1:g}px)}}")
        kf.append(f"100%{{transform:translateY({-self.offset:g}px)}}")
        self.add_style(f"@keyframes scroll{{{''.join(kf)}}}.scroll{{animation:scroll {total:.2f}s linear {iters}}}")
