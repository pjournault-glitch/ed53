import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

TRIM_FR = ['1er trimestre', '2ème trimestre', '3ème trimestre']

MARGIN = 12 * mm
HEADER_HEIGHT = 18 * mm   # place réservée en haut de chaque page pour le titre et le sous-titre


class MealController:
    def __init__(self, participants, title: str, subtitle: str, extra_rows: int = 3):
        self.participants = participants
        self.title = title
        self.subtitle = subtitle
        self.extra_rows = extra_rows
        self.trimestres = TRIM_FR
        self._total_pages = None

    def generate(self) -> bytes:
        """Renvoie le PDF (en octets) : une ligne par participant, une colonne par mois."""
        if not self.participants:
            raise ValueError("Aucun participant. Merci de renseigner d'abord les participants.")
        _, pages = self._build(total_pages=None)    # 1re passe : compte les pages
        pdf, _ = self._build(total_pages=pages)     # 2e passe : « Page n/total »
        return pdf

    def _build(self, total_pages: int | None) -> tuple[bytes, int]:
        self._total_pages = total_pages
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(A4), title=self.title,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN + HEADER_HEIGHT, bottomMargin=MARGIN + 5 * mm,
        )

        ordered = sorted(self.participants, key=lambda p: ((p.name or '').casefold(), (p.firstname or '').casefold()))
        blank = [''] * len(self.trimestres)
        data = [['Nom', 'Prénom', *self.trimestres]]
        data += [[(p.name or '').upper(), p.firstname or '', *blank] for p in ordered]
        data += [['', '', *blank] for _ in range(self.extra_rows)]   # lignes libres pour les ajouts de dernière minute

        w_name, w_first = 50 * mm, 40 * mm
        w_month = (doc.width - w_name - w_first) / len(self.trimestres)
        table = Table(
            data,
            colWidths=[w_name, w_first] + [w_month] * len(self.trimestres),
            rowHeights=[9 * mm] + [11 * mm] * (len(data) - 1),
            repeatRows=1,                                      # l'en-tête du tableau se répète à chaque page
        )
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (-1, 0), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))

        doc.build([table], onFirstPage=self._decorate, onLaterPages=self._decorate)
        return buffer.getvalue(), doc.page    # doc.page = numéro de la dernière page = nombre de pages

    def _decorate(self, canvas, doc):
        """Dessine sur chaque page : titre, sous-titre et « Page n/total »."""
        width, height = doc.pagesize
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(width / 2, height - MARGIN - 6 * mm, self.title)
        if self.subtitle:
            canvas.setFont('Helvetica', 10)
            canvas.drawCentredString(width / 2, height - MARGIN - 13 * mm, self.subtitle)
        canvas.setFont('Helvetica', 8)
        total = self._total_pages or doc.page
        canvas.drawRightString(width - MARGIN, 8 * mm, f"Page {doc.page}/{total}")
        canvas.restoreState()