import re
from pathlib import Path
from nicegui import ui

HELP_FILE = Path(__file__).resolve().parent.parent / 'assets' / 'aide.md'
DEFAULT_TEXT = "# Aide\n\nLe guide d'utilisation n'est pas encore disponible."


class HelpTab:
    def __init__(self):
        text = self._strip_toc(self._read_help())
        headings = self._headings(text)

        # hauteur fixe : chaque colonne défile dans son propre cadre
        with ui.row().classes('w-full no-wrap gap-6 items-stretch') \
                .style('height: calc(100vh - 120px)'):

            # colonne de gauche : le sommaire, qui ne bouge pas quand on lit
            with ui.column().classes('gt-sm w-64 shrink-0 gap-0 overflow-y-auto pr-2'):
                ui.label('Sommaire').classes('text-subtitle2 text-bold').style('line-height: 1.5; margin-bottom: 4px')
                for index, (level, title) in enumerate(headings):
                    if level > 3:
                        continue
                    ui.label(title).classes('cursor-pointer text-primary') \
                        .style(f'padding-left: {(level - 1) * 12}px; font-size: 13px; line-height: 1.25; margin: 1px') \
                        .on('click', lambda _, i=index: self._scroll_to(i))

            # colonne de droite : le texte de l'aide, avec sa propre barre de défilement
            with ui.element('div').classes('grow min-w-0 overflow-y-auto bg-white rounded-borders p-6'):
                self._markdown = ui.markdown(
                    text, extras=['fenced-code-blocks', 'tables', 'header-ids']
                ).classes('aide-md')

    def _scroll_to(self, index: int) -> None:
        ui.run_javascript(f'''
            const root = document.getElementById("{self._markdown.html_id}");
            const h = root && root.querySelectorAll("h1,h2,h3,h4,h5,h6")[{index}];
            if (h) h.scrollIntoView({{behavior: "smooth", block: "start"}});
        ''')

    @staticmethod
    def _headings(text: str) -> list[tuple[int, str]]:
        result, in_code = [], False
        for line in text.splitlines():
            if line.strip().startswith('```'):
                in_code = not in_code
                continue
            if not in_code and (m := re.match(r'^(#{1,6})\s+(.+?)\s*#*\s*$', line)):
                result.append((len(m.group(1)), m.group(2)))
        return result

    @staticmethod
    def _strip_toc(text: str) -> str:
        """Retire la section « Table des matières » écrite à la main."""
        return re.sub(r'^## Table des matières\s*\n.*?(?=^## )', '', text,
                      count=1, flags=re.S | re.M)

    @staticmethod
    def _read_help() -> str:
        try:
            return HELP_FILE.read_text(encoding='utf-8')
        except OSError:
            return DEFAULT_TEXT