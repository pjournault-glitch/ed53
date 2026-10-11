import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PADDING = 3 * mm
LINE_SPACING = 1.2
MIN_FONT_SIZE = 8
FALLBACK_FONT = 'Helvetica-Bold'


class BadgeController:
    def __init__(self, persons, tag, logo_path, skip: int = 0, fill_page: bool = True,
                 draw_borders: bool = True, font_path: str | None = None,
                 font_size: float = 18, logo_height: float = 14 * mm):
        self.persons = persons
        self.tag = tag                      # Tag : marges en mm, nb_horizontal, nb_vertical
        self.logo_path = logo_path
        self.skip = skip                    # badges déjà utilisés sur la 1re feuille
        self.fill_page = fill_page          # complète la dernière page avec des badges vierges
        self.draw_borders = draw_borders    # traits de découpe
        self.font = self._register_font(font_path)
        self.font_size = font_size
        self.logo_height = logo_height

    @staticmethod
    def _register_font(font_path: str | None) -> str:
        """Enregistre la police TrueType (gras) ; Helvetica-Bold si elle est introuvable."""
        if font_path and Path(font_path).exists():
            pdfmetrics.registerFont(TTFont('BadgeFont', str(font_path)))
            return 'BadgeFont'
        return FALLBACK_FONT

    def generate(self) -> bytes:
        tag = self.tag
        page_w, page_h = A4
        cell_w = (page_w - (tag.margin_left + tag.margin_right) * mm) / tag.nb_horizontal
        cell_h = (page_h - (tag.margin_top + tag.margin_bottom) * mm) / tag.nb_vertical
        per_page = tag.nb_horizontal * tag.nb_vertical

        ordered = sorted(self.persons, key=lambda p: ((p.name or '').casefold(), (p.firstname or '').casefold()))
        badges = [p for p in ordered if (p.firstname or '').strip() or (p.name or '').strip()]
        if self.fill_page:
            remainder = (-(len(badges) + self.skip)) % per_page
            badges += [None] * remainder          # badges vierges (logo seul)

        logo = ImageReader(str(self.logo_path))
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        current_page = 0
        for i, person in enumerate(badges):
            page, slot = divmod(i + self.skip, per_page)
            if page != current_page:
                c.showPage()
                current_page = page
            row, col = divmod(slot, tag.nb_horizontal)
            x = tag.margin_left * mm + col * cell_w
            y_top = page_h - tag.margin_top * mm - row * cell_h
            if self.draw_borders:
                c.setStrokeColor(colors.HexColor('#b5b58a'))
                c.setLineWidth(0.3)
                c.rect(x, y_top - cell_h, cell_w, cell_h)
            self._draw_badge(c, logo, person, x, y_top, cell_w, cell_h)

        c.save()
        return buffer.getvalue()

    def _draw_badge(self, c, logo, person, x, y_top, w, h):
        # logo en haut à gauche, en conservant ses proportions
        iw, ih = logo.getSize()
        logo_w = self.logo_height * iw / ih
        c.drawImage(logo, x + PADDING, y_top - PADDING - self.logo_height,
                    width=logo_w, height=self.logo_height, mask='auto')
        if person is None:
            return

        # zone du texte : sous le logo
        inner_w = w - 2 * PADDING
        zone_top = y_top - PADDING - self.logo_height
        zone_bottom = y_top - h + PADDING
        zone_h = zone_top - zone_bottom

        firstname = (person.firstname or '').strip()
        name = (person.name or '').strip()

        def split(size):
            lines = []
            for text in (firstname, name):
                if text:
                    lines += simpleSplit(text, self.font, size, inner_w)
            return lines

        size = self.font_size
        lines = split(size)
        while size > MIN_FONT_SIZE and lines and (
            len(lines) * size * LINE_SPACING > zone_h
            or max(stringWidth(l, self.font, size) for l in lines) > inner_w
        ):
            size -= 0.5
            lines = split(size)

        block = len(lines) * size * LINE_SPACING
        y = zone_top - (zone_h - block) / 2 - size      # bloc centré verticalement
        c.setFont(self.font, size)
        for line in lines:
            c.drawCentredString(x + w / 2, y, line)     # et horizontalement
            y -= size * LINE_SPACING