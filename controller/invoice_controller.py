import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

FONT, BOLD, ITALIC = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'
TEAL = colors.HexColor('#1b5a78')
PAGE_W, PAGE_H = A4

LEFT = 11            # marge gauche (mm)
NAMES_X = 36.5       # colonne des noms de participants (mm)
AMOUNT_X = 164.8     # bord droit de la colonne des montants (mm)


def _y(top_mm: float) -> float:
    """Convertit une position « mm depuis le haut de la page » en coordonnée ReportLab."""
    return PAGE_H - top_mm * mm


def _text(c, x_mm, top_mm, s, font=FONT, size=10.0, align='left',
          color=colors.black, max_width_mm=None):
    """Écrit un texte centré verticalement sur top_mm ; réduit la police s'il dépasse max_width_mm."""
    if max_width_mm:
        while size > 6 and stringWidth(s, font, size) > max_width_mm * mm:
            size -= 0.5
    c.setFillColor(color)
    c.setFont(font, size)
    x, y = x_mm * mm, _y(top_mm) - size * 0.35
    if align == 'right':
        c.drawRightString(x, y, s)
    elif align == 'center':
        c.drawCentredString(x, y, s)
    else:
        c.drawString(x, y, s)


class InvoiceController:
    def __init__(self, participants, senders, information, fee: float, logo_path,
                 formation_name: str = 'Ecole du Diocèse', school_year: str = '', year: int = 1,
                 invoice_date: date | None = None, first_number: int | None = None,
                 service_label: str = 'Service de la formation permanente',
                 organisation_line: str = 'Diocèse de Laval'):
        self.participants = participants
        self.senders = senders
        self.info = information               # Information : name, street, bp, zip, city, phone, mail, bic, iban
        self.fee = float(fee)                 # tarif par participant
        self.logo = ImageReader(str(logo_path))
        self.formation_name = formation_name
        self.school_year = school_year        # ex. '2026-2027'
        self.year = year
        self.date = invoice_date or date.today()
        self.first_number = first_number      # None : « Note de frais n° » laissé vide, à compléter à la main
        self.service_label = service_label
        self.organisation_line = organisation_line
        self.without_sender: list = []     # participants sans envoyant renseigné
        self.unknown_sender: list = []     # participants dont l'envoyant n'est pas dans la liste
        self._groups = self._group()

    # --- regroupement participants -> envoyant -------------------------------

    def _group(self) -> list[tuple]:
        by_label = {s.label: s for s in self.senders}
        groups: dict[str, list] = {}
        ordered = sorted(self.participants,
                         key=lambda p: ((p.name or '').casefold(), (p.firstname or '').casefold()))
        for p in ordered:
            if not ((p.firstname or '').strip() or (p.name or '').strip()):
                continue                                      # ligne vide
            label = (p.sender_label or '').strip()
            if not label:
                self.without_sender.append(p)
                continue
            if label not in by_label:
                self.unknown_sender.append(p)
                continue
            groups.setdefault(label, []).append(p)
        return sorted(
            ((by_label[label], people) for label, people in groups.items()),
            key=lambda g: ((g[0].name or g[0].organisation or '').casefold(),
                           (g[0].firstname or '').casefold()),
        )
    
    @staticmethod
    def _person(s) -> str:
        """Identité de l'envoyant (titre prénom nom) ; vide s'il n'a qu'une organisation."""
        if not ((s.firstname or '').strip() or (s.name or '').strip()):
            return ''
        return ' '.join(x.strip() for x in (s.title, s.firstname, s.name) if x and x.strip())

    @staticmethod
    def _full_name(p) -> str:
        return ' '.join(x.strip() for x in (p.firstname, p.name) if x and x.strip())

    # --- génération ---------------------------------------------------------

    def generate(self) -> bytes:
        if not self._groups:
            raise ValueError("Aucun participant rattaché à un envoyant")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setTitle('Factures')
        for i, (sender, people) in enumerate(self._groups):
            if i:
                c.showPage()
            number = None if self.first_number is None else self.first_number + i
            self._draw(c, sender, people, number)
        c.save()
        return buffer.getvalue()

    def _draw(self, c, sender, people, number):
        info, n = self.info, len(people)
        total = f'{self.fee * n:.2f} €'
        person = self._person(sender)

        # --- en-tête : logo, service, numéro et date -------------------------
        iw, ih = self.logo.getSize()
        logo_h = 22 * mm
        c.drawImage(self.logo, LEFT * mm, _y(8) - logo_h, width=logo_h * iw / ih,
                    height=logo_h, mask='auto')
        _text(c, LEFT, 34, self.service_label, BOLD, 11, color=TEAL)
        _text(c, 135, 10, 'Note de frais n°' + (f' {number}' if number is not None else ''))
        _text(c, 196.5, 15.2, f'Date   {self.date:%d/%m/%Y}', align='right')

        # --- encadré DESTINATAIRE --------------------------------------------
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.7)
        c.rect(95.5 * mm, _y(56), 105 * mm, 29 * mm)
        c.line(95.5 * mm, _y(32), 200.5 * mm, _y(32))
        _text(c, 148, 29.3, 'DESTINATAIRE', align='center')

        slots = [34.3, 39.2, 44.0, 48.9, 53.8]        # 5 lignes : organisation, personne, rue (2), ville
        if sender.organisation:
            _text(c, 148, slots[0], sender.organisation.strip(), max_width_mm=100, align='center')
        if person:
            _text(c, 148, slots[1], person, BOLD, max_width_mm=100, align='center')
        street = [l.strip() for l in (sender.street or '').splitlines() if l.strip()]
        if len(street) > 2:
            street = [street[0], ', '.join(street[1:])]
        for i, line in enumerate(street):              # la rue se place juste au-dessus de la ville
            _text(c, 148, slots[4 - len(street) + i], line, max_width_mm=100, align='center')
        town = ' '.join(x.strip() for x in (sender.zip, (sender.city or '').upper()) if x and x.strip())
        if town:
            _text(c, 148, slots[4], town, max_width_mm=100, align='center')

        # --- émetteur et formation -------------------------------------------
        _text(c, LEFT, 57.6, info.name, BOLD, 11)
        _text(c, LEFT, 62.6, self.organisation_line, BOLD, 11)
        _text(c, LEFT, 77.5, f'FORMATION : {self.formation_name} {self.school_year} (année {self.year}-{self.year+1})'.strip())

        # --- tableau des participants ----------------------------------------
        _text(c, NAMES_X, 92, 'Participants', BOLD)
        _text(c, 164.5, 92, 'Total €uros', BOLD, align='right')
        row_h = max(3.0, min(4.8, 83.0 / max(n - 1, 1)))    # se resserre s'il y a beaucoup de participants
        first_row = 96.9
        for i, p in enumerate(people):
            top = first_row + i * row_h
            _text(c, NAMES_X, top, self._full_name(p))
            _text(c, AMOUNT_X, top, f'{self.fee:.2f} €', align='right')
        rule_y = first_row + (n - 1) * row_h + 7.2
        c.line(134 * mm, _y(rule_y), 166.8 * mm, _y(rule_y))
        _text(c, 96.7, rule_y + 6.9, 'Total à payer :', BOLD, 12)
        _text(c, AMOUNT_X, rule_y + 6.9, total, BOLD, 12, align='right')

        # --- pied de page : coordonnées et compte ----------------------------
        iban = (info.iban or '').replace(' ', '')
        iban = ' '.join(iban[i:i + 4] for i in range(0, len(iban), 4))
        town_info = ' '.join(x for x in (info.zip, info.city) if x)
        address = ' - '.join(x for x in (info.addressee, info.street, info.bp, town_info) if x)
        _text(c, 105, 202.4, address, align='center')
        _text(c, 105, 207.3, f'Tel. : {info.phone} - e-mail : {info.mail}', align='center')
        _text(c, 105, 212.2, f'Compte {info.name.capitalize()} : BIC : {info.bic} IBAN {iban}', align='center')

        # --- coupon à découper -----------------------------------------------
        c.setLineWidth(0.5)
        c.setDash(2, 2)
        c.line(10.3 * mm, _y(219.4), 201 * mm, _y(219.4))
        c.setDash()
        _text(c, 105, 222.8, 'Partie à découper et à joindre à votre règlement - merci',
              ITALIC, 9.5, align='center')

        title_y = 231
        _text(c, 105, title_y, self.formation_name, size=12, align='center')
        half = stringWidth(self.formation_name, FONT, 12) / 2
        c.line(PAGE_W / 2 - half, _y(title_y) - 12 * 0.35 - 1.5,
               PAGE_W / 2 + half, _y(title_y) - 12 * 0.35 - 1.5)

        _text(c, LEFT, 241.3, f'Envoyant: {person}'.rstrip())
        _text(c, LEFT, 246.1, 'Participants:')
        cols = 1 if n <= 5 else 2 if n <= 10 else 3        # plusieurs colonnes au-delà de 5 participants
        per_col = -(-n // cols)
        slip_h = min(4.75, 24.0 / max(per_col - 1, 1))
        for i, p in enumerate(people):
            col, row = divmod(i, per_col)
            _text(c, NAMES_X + col * 55, 251 + row * slip_h, self._full_name(p))

        label = f"Montant réglé par chèque ci-joint, à l'ordre de {info.name.lower()} :"
        _text(c, LEFT, 279.5, label)
        _text(c, LEFT + stringWidth(label, FONT, 10) / mm + 3, 279.5, total, BOLD, 12)