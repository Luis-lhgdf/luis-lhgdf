#!/usr/bin/env python3
"""Gera os SVGs animados do README de perfil (estilo "sessão de terminal").

  assets/terminal.svg / terminal-mobile.svg — sessão: neofetch → cat stack.txt → cat projetos.txt → git log
  assets/contrib.svg  / contrib-mobile.svg  — card fixo git log --graph (heatmap + streaks)

Uso:
    python scripts/main.py            # busca dados reais e gera os quatro SVGs
    python scripts/main.py --offline  # usa só os snapshots locais (scripts/*-data.json)
Variáveis: GITHUB_TOKEN (opcional; evita rate limit no Actions).

Módulos: config.py (textos e paleta) · github_data.py (dados) · svg.py (janela/sessão) ·
heatmap.py (grade de contribuições) · terminal.py (hero) · contrib.py (card).
"""
from __future__ import annotations

import sys

from config import ASSETS, DESKTOP, MOBILE
from contrib import build_contrib
from github_data import load_contrib_data, load_terminal_data, streaks
from terminal import build_terminal


def write(name: str, svg: str) -> None:
    path = ASSETS / name
    path.write_text(svg, encoding="utf-8")
    print(f"ok: assets/{name} ({path.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    offline = "--offline" in sys.argv
    tdata = load_terminal_data(offline)
    cdata = load_contrib_data(offline)
    write("terminal.svg", build_terminal(tdata, cdata, DESKTOP))
    write("terminal-mobile.svg", build_terminal(tdata, cdata, MOBILE))
    write("contrib.svg", build_contrib(cdata, DESKTOP, weeks=52))
    write("contrib-mobile.svg", build_contrib(cdata, MOBILE, weeks=26))
    total, current, longest = streaks(cdata["days"])
    print(f"   repos={tdata['repos']} stars={tdata['stars']} followers={tdata['followers']} · "
          f"contribuições={total} streak={current} recorde={longest}")


if __name__ == "__main__":
    main()
