from nicegui import ui

def required_label(field, text):
    with field.add_slot('label'):
        ui.html(f'{text} <span class="text-red">*</span>')
    return field

required_rule = {'Champ obligatoire': lambda v: v is not None and str(v).strip() != ''}
