from datetime import date
import io

from reportlab.lib.fonts import tt2ps
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PADDING = 3 * mm
TOP_PADDING = 5 * mm
LINE_SPACING = 1.2
MIN_FONT_SIZE = 5
GAP = 4 * mm   # espace minimal entre l'intervenant et la date


class FileLabelController:
    def __init__(self, persons, intervention: dict, tag, skip: int = 0, draw_borders: bool = False,
                 font_name: str = 'Helvetica', font_size: float = 10,
                 extra_identities: tuple[str, ...] = ()):
        self.persons = persons
        self.intervention = intervention   # {'speaker': ..., 'title': ..., 'date': date ou texte}
        self.tag = tag                     # Tag : marges en mm, nb_horizontal, nb_vertical
        self.skip = skip                   # étiquettes déjà utilisées sur la 1re feuille
        self.draw_borders = draw_borders
        self.font_name = font_name
        self.font_bold = tt2ps(font_name, 1, 0)     # Helvetica -> Helvetica-Bold
        self.font_italic = tt2ps(font_name, 0, 1)   # Helvetica -> Helvetica-Oblique
        self.font_size = font_size
        self.extra_identities = extra_identities    # étiquettes ajoutées à la fin, ex. ('INTERVENANT', 'ARCHIVE')

    @staticmethod
    def _identity(p) -> str:
        return ' '.join(x.strip() for x in [p.title, p.firstname, p.name] if x and x.strip())

    @staticmethod
    def _format_date(value) -> str:
        if isinstance(value, date):
            return value.strftime('%d/%m/%Y')
        return str(value or '')

    def generate(self) -> bytes:
        tag = self.tag
        page_w, page_h = A4
        cell_w = (page_w - (tag.margin_left + tag.margin_right) * mm) / tag.nb_horizontal
        cell_h = (page_h - (tag.margin_top + tag.margin_bottom) * mm) / tag.nb_vertical
        per_page = tag.nb_horizontal * tag.nb_vertical

        ordered = sorted(self.persons, key=lambda p: ((p.name or '').casefold(), (p.firstname or '').casefold()))
        identities = [i for i in (self._identity(p) for p in ordered) if i]
        identities += list(self.extra_identities)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        current_page = 0
        for i, identity in enumerate(identities):
            page, slot = divmod(i + self.skip, per_page)
            if page != current_page:
                c.showPage()
                current_page = page
            row, col = divmod(slot, tag.nb_horizontal)
            x = tag.margin_left * mm + col * cell_w
            y_top = page_h - tag.margin_top * mm - row * cell_h
            if self.draw_borders:
                c.setLineWidth(0.3)
                c.rect(x, y_top - cell_h, cell_w, cell_h)
            self._draw_label(c, identity, x, y_top, cell_w, cell_h)

        c.save()
        return buffer.getvalue()

    @staticmethod
    def _fit(text: str, font: str, size: float, max_width: float) -> float:
        """Réduit la police jusqu'à ce que le texte tienne sur une ligne."""
        while size > MIN_FONT_SIZE and stringWidth(text, font, size) > max_width:
            size -= 0.5
        return size

    def _draw_label(self, c, identity: str, x, y_top, w, h):
        inner_w = w - 2 * PADDING
        left, right = x + PADDING, x + w - PADDING
        top, bottom = y_top - TOP_PADDING, y_top - h + TOP_PADDING

        speaker = str(self.intervention.get('speaker') or '')
        title = str(self.intervention.get('title') or '')
        when = self._format_date(self.intervention.get('date'))

        # --- haut : identité de la personne ---
        id_size = self._fit(identity, self.font_name, self.font_size, inner_w)
        c.setFont(self.font_name, id_size)
        c.drawCentredString(x + w / 2, top - id_size, identity)
        id_h = id_size * LINE_SPACING

        # --- bas : intervenant à gauche, date à droite (italique) ---
        b_size = self.font_size - 1
        while b_size > MIN_FONT_SIZE and (
            stringWidth(speaker, self.font_italic, b_size)
            + stringWidth(when, self.font_italic, b_size) + GAP > inner_w
        ):
            b_size -= 0.5
        c.setFont(self.font_italic, b_size)
        c.drawString(left, bottom, speaker)
        c.drawRightString(right, bottom, when)
        bottom_h = b_size * LINE_SPACING

        # --- milieu : titre en gras, sur plusieurs lignes si besoin, centré dans l'espace restant ---
        if not title:
            return
        zone_top = top - id_h
        zone_bottom = bottom + bottom_h
        zone_h = zone_top - zone_bottom

        t_size = self.font_size
        lines = simpleSplit(title, self.font_bold, t_size, inner_w)
        while t_size > MIN_FONT_SIZE and (
            len(lines) * t_size * LINE_SPACING > zone_h
            or max(stringWidth(l, self.font_bold, t_size) for l in lines) > inner_w
        ):
            t_size -= 0.5
            lines = simpleSplit(title, self.font_bold, t_size, inner_w)

        block = len(lines) * t_size * LINE_SPACING
        y = zone_top - (zone_h - block) / 2 - t_size      # bloc centré verticalement
        c.setFont(self.font_bold, t_size)
        for line in lines:
            c.drawCentredString(x + w / 2, y, line)       # et horizontalement
            y -= t_size * LINE_SPACING