"""Configuração: caminhos, paleta, textos e grade tipográfica dos SVGs do README.

É AQUI que se editam os textos que aparecem no terminal animado (FIELDS, STACK, PROJECTS).
Depois de editar, rode:  python scripts/main.py --offline
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_PATH = ASSETS / "fonts" / "JetBrainsMono-subset.woff2"
TERMINAL_DATA = ROOT / "scripts" / "terminal-data.json"
CONTRIB_DATA = ROOT / "scripts" / "contrib-data.json"

USER = "Luis-lhgdf"          # usuário do GitHub (API + página de contribuições)
PROFILE_REPO = "luis-lhgdf"  # repositório do perfil (ignorado nas estatísticas)
PROMPT_STR = "luis@backend:~$ "

# ---------------------------------------------------------------- paleta (GitHub Primer Dark)
C = {
    "canvas": "#0D1117", "surface": "#161B22", "border": "#30363D", "track": "#21262D",
    "text": "#C9D1D9", "bright": "#E6EDF3", "muted": "#8B949E", "dim": "#484F58",
    "green": "#3FB950", "green_dim": "#238636", "blue": "#58A6FF", "cyan": "#39C5CF",
    "yellow": "#D29922", "tl_red": "#FF5F56", "tl_yellow": "#FFBD2E", "tl_green": "#27C93F",
}
PALETTE = ["#484F58", "#FF7B72", "#3FB950", "#D29922", "#58A6FF", "#BC8CFF", "#39C5CF", "#B1BAC4"]
HEAT = ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"]  # níveis 0..4 do heatmap
LANG_COLORS = {
    "Python": "#3572A5", "HTML": "#E34C26", "CSS": "#663399", "SCSS": "#C6538C",
    "PowerShell": "#012456", "JavaScript": "#F1E05A", "Shell": "#89E051", "TypeScript": "#3178C6",
    "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384D54", "SQL": "#E38C00",
}
LANG_ALIAS = {"SCSS": "CSS", "Less": "CSS"}  # dialetos agrupados na barra de linguagens

# ---------------------------------------------------------------- textos do terminal
LOGO = [  # figlet ANSI Shadow "luis" → só os '█' viram retângulos
    "██╗     ██╗   ██╗██╗███████╗",
    "██║     ██║   ██║██║██╔════╝",
    "██║     ██║   ██║██║███████╗",
    "██║     ██║   ██║██║╚════██║",
    "███████╗╚██████╔╝██║███████║",
    "╚══════╝ ╚═════╝ ╚═╝╚══════╝",
]

# `neofetch --profile` — chave (até 8 caracteres) e valor
FIELDS = [
    ("Role", "Backend Developer · Python"),
    ("Base", "São Paulo, Brasil"),
    ("Build", "APIs FastAPI · automação · dados & BI"),
    ("Deploy", "Linux · Docker · NGINX"),
    ("Now", "RAG com LLMs locais · JWT/OAuth2 · Superset"),
    ("Web", "luis-lhgdf.github.io/portfolio"),
    ("Mail", "luis.dev_@outlook.com"),
    ("LinkedIn", "linkedin.com/in/luis-henrique-281b97186"),
]

# `cat stack.txt` — grupo (até 15 caracteres) e itens
STACK = [
    ("backend", ["Python", "FastAPI", "SQL", "Alembic"]),
    ("infra", ["Docker", "NGINX", "Linux", "Bash", "Git", "GitHub Actions"]),
    ("dados", ["MySQL", "MariaDB", "PostgreSQL", "Superset"]),
    ("automação & ia", ["Selenium", "Ollama", "Open WebUI", "GLPI"]),
]

# `cat projetos.txt` — repositório (até 25 caracteres) e stack; no terminal só aparecem nome + stack
# (a descrição completa fica na tabela fixa do README.md)
PROJECTS = [
    ("python-world", "Python · customtkinter · OpenAI API"),
    ("sys-comercial", "Python · SQL"),
    ("claudecode-usage-widget", "Python · PowerShell · Windows"),
]

MONTHS_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------------------------------------------------------- geometria
BAR_H = 32                               # barra de título da janela
LOGO_CELL_W, LOGO_CELL_H = 8.0, 12.5     # célula do logo pixel-art


@dataclass(frozen=True)
class Grid:
    """Grade tipográfica de uma variante (desktop / mobile)."""
    W: int = 760      # largura da janela
    PAD: int = 24     # margem lateral
    FS: float = 13    # tamanho da fonte

    @property
    def CW(self) -> float:  # largura de um caractere (JetBrains Mono: 600/1000 em)
        return self.FS * 0.6

    @property
    def LH(self) -> int:    # altura de linha
        return int(self.FS + 5)

    def cols(self, x: float) -> int:
        """Quantos caracteres cabem de x até a margem direita."""
        return int((self.W - self.PAD - x) // self.CW)


DESKTOP = Grid(W=760, PAD=24, FS=13)
MOBILE = Grid(W=420, PAD=16, FS=14)
