from datetime import date, datetime
from nicegui import ui

def required_label(field, text):
    with field.add_slot('label'):
        ui.html(f'{text} <span class="text-red">*</span>')
    return field

required_rule = {'Champ obligatoire': lambda v: v is not None and str(v).strip() != ''}

def required(v) -> bool:
    return bool(v and v.strip())

def valid_date(v) -> bool:
    try:
        datetime.strptime(v or '', '%d/%m/%Y')
        return True
    except ValueError:
        return False

def to_display(value) -> str:
    """Convertit une date (objet date, datetime ou texte ISO) en JJ/MM/AAAA."""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value).strftime('%d/%m/%Y')
        except ValueError:
            return value          # déjà au bon format, ou texte libre
    return ''  

