"""Dados reais do GitHub: API (repos, stars, followers, linguagens) e página pública de contribuições.

Cada carregador grava um snapshot JSON e cai nele quando a rede falha (rate limit, offline).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from datetime import date

from config import CONTRIB_DATA, LANG_ALIAS, PROFILE_REPO, TERMINAL_DATA, USER


def fetch(url: str, accept: str = "application/vnd.github+json") -> bytes:
    headers = {"User-Agent": "Mozilla/5.0 readme-svgs", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
        return resp.read()


def fetch_json(url: str) -> object:
    return json.loads(fetch(url))


def load_terminal_data(offline: bool) -> dict:
    """repos públicos (sem forks e sem o repo do perfil), stars, followers, ano de entrada e bytes por linguagem."""
    if not offline:
        try:
            user = fetch_json(f"https://api.github.com/users/{USER}")
            repos = fetch_json(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
            langs: dict[str, int] = {}
            stars = count = 0
            for r in repos:
                if r["fork"] or r["name"].lower() == PROFILE_REPO:
                    continue
                count += 1
                stars += r["stargazers_count"]
                for k, v in fetch_json(r["languages_url"]).items():
                    langs[k] = langs.get(k, 0) + v
            data = {"repos": count, "stars": stars, "followers": user["followers"],
                    "since": user["created_at"][:4],
                    "langs": dict(sorted(langs.items(), key=lambda kv: -kv[1]))}
            TERMINAL_DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return data
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] API indisponível ({exc}); usando snapshot", file=sys.stderr)
    return json.loads(TERMINAL_DATA.read_text(encoding="utf-8"))


def load_contrib_data(offline: bool) -> dict:
    """Um dia por célula do gráfico de contribuições: date, row (0=dom), col (semana), level (0-4), count."""
    if not offline:
        try:
            html = fetch(f"https://github.com/users/{USER}/contributions", accept="text/html").decode("utf-8")
            cells = re.findall(
                r'<td[^>]*?data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="(contribution-day-component-(\d)-(\d+))"'
                r'[^>]*?data-level="(\d)"', html)
            tips = dict(re.findall(
                r'<tool-tip[^>]*for="(contribution-day-component-\d-\d+)"[^>]*>([^<]*)</tool-tip>', html))
            days = []
            for d, cid, row, col, level in cells:
                m = re.match(r"(\d+)", tips.get(cid, ""))
                days.append({"date": d, "row": int(row), "col": int(col), "level": int(level),
                             "count": int(m.group(1)) if m else 0})
            if len(days) < 300:
                raise ValueError(f"parse retornou só {len(days)} dias")
            days.sort(key=lambda x: x["date"])
            data = {"fetched": date.today().isoformat(), "days": days}
            CONTRIB_DATA.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
            return data
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] contribuições indisponíveis ({exc}); usando snapshot", file=sys.stderr)
    return json.loads(CONTRIB_DATA.read_text(encoding="utf-8"))


def streaks(days: list[dict]) -> tuple[int, int, int]:
    """(total, streak atual, maior streak). Hoje sem commit ainda não quebra o streak."""
    total = sum(d["count"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif d["date"] == days[-1]["date"]:
            continue
        else:
            break
    return total, current, longest


def top_langs(langs: dict[str, int], n: int = 3) -> list[tuple[str, float]]:
    """Top-n linguagens em % (dialetos agrupados) + "Outros"."""
    merged: dict[str, int] = {}
    for k, v in langs.items():
        k = LANG_ALIAS.get(k, k)
        merged[k] = merged.get(k, 0) + v
    items = sorted(merged.items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in items) or 1
    head = [(k, 100 * v / total) for k, v in items[:n]]
    rest = sum(100 * v / total for _, v in items[n:])
    if rest >= 1:
        head.append(("Outros", rest))
    return head
