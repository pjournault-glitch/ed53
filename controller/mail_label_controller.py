import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PADDING = 3 * mm
LINE_SPACING = 1.2


class MailLabelController:
    def __init__(self, persons, tag, skip: int = 0, draw_borders: bool = False,
                 font_name: str = 'Helvetica', font_size: float = 10):
        self.persons = persons
        self.tag = tag                  # Tag : marges en mm, nb_horizontal, nb_vertical
        self.skip = skip                # étiquettes déjà utilisées sur la 1re feuille
        self.draw_borders = draw_borders
        self.font_name = font_name
        self.font_size = font_size

    @staticmethod
    def _lines(p) -> list[str]:
        identity = ' '.join(x for x in [p.title, p.firstname, (p.name or '').upper()] if x and x.strip())
        street = [l.strip() for l in (p.street or '').splitlines() if l.strip()]
        town = ' '.join(x for x in [p.zip, (p.city or '').upper()] if x and x.strip())
        return [l for l in [identity, *street, town] if l]

    def generate(self) -> bytes:
        if not self.persons:
            raise ValueError("Aucun participant. Merci de renseigner d'abord les participants.")        
        tag = self.tag
        page_w, page_h = A4
        cell_w = (page_w - (tag.margin_left + tag.margin_right) * mm) / tag.nb_horizontal
        cell_h = (page_h - (tag.margin_top + tag.margin_bottom) * mm) / tag.nb_vertical
        per_page = tag.nb_horizontal * tag.nb_vertical

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        ordered = sorted(self.persons, key=lambda p: ((p.name or '').casefold(), (p.firstname or '').casefold()))
        persons = [p for p in ordered if self._lines(p)]

        current_page = 0
        for i, person in enumerate(persons):
            pos = i + self.skip
            page, slot = divmod(pos, per_page)
            if page != current_page:
                c.showPage()
                current_page = page
            row, col = divmod(slot, tag.nb_horizontal)
            x = tag.margin_left * mm + col * cell_w
            y_top = page_h - tag.margin_top * mm - row * cell_h
            if self.draw_borders:
                c.setLineWidth(0.3)
                c.rect(x, y_top - cell_h, cell_w, cell_h)
            self._draw_label(c, self._lines(person), x, y_top, cell_w, cell_h)

        c.save()
        return buffer.getvalue()

    def _draw_label(self, c, lines, x, y_top, w, h):
        # réduit la police jusqu'à ce que le texte tienne dans l'étiquette
        size = self.font_size
        while size > 5 and (
            len(lines) * size * LINE_SPACING > h - 2 * PADDING
            or max(stringWidth(l, self.font_name, size) for l in lines) > w - 2 * PADDING
        ):
            size -= 0.5
        block = len(lines) * size * LINE_SPACING
        y = y_top - (h - block) / 2 - size          # bloc centré verticalement
        c.setFont(self.font_name, size)
        for line in lines:
            c.drawString(x + PADDING, y, line)
            y -= size * LINE_SPACING