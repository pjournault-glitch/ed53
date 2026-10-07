from datetime import date
import json
import os
from pathlib import Path
import re
from nicegui import ui
from controller.database_controller import database_controller
from model.model import Information, Promotion
from util.util import required_label, required_rule

def is_valid_iban(value: str) -> bool:
    iban = value.replace(' ', '').upper()
    if not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]{11,30}', iban):
        return False
    rearranged = iban[4:] + iban[:4]
    digits = ''.join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


class InformationTab:
    def __init__(self, promotion:Promotion):
        self.promotion = promotion
        info = promotion.information
        with ui.row().classes('w-full no-wrap gap-8'):
            with ui.column():
                self.name = required_label(ui.input('Nom', validation=required_rule, value=info.name).classes('w-full'), 'Nom')
                self.addressee = required_label(ui.input("À l'attention de", validation=required_rule, value=info.addressee).classes('w-full'),"À l'attention de")
                self.street = required_label(ui.input('Rue', validation=required_rule, value=info.street).classes('w-full'),'Rue')
                self.bp = ui.input('Boîte postale', value=info.bp).classes('w-full')
                with ui.row().classes('w-full no-wrap'):
                    self.zip_code = required_label(ui.input('Code postal', validation=required_rule, value=info.zip).props('mask=##### maxlength=5').classes('w-32'),'Code postal')
                    self.town = required_label(ui.input('Ville', validation=required_rule, value=info.city).classes('grow'),"Ville")
                self.phone = ui.input('Téléphone', value=info.phone).props('type=tel mask="## ## ## ## ##"').classes('w-full')
                self.email = ui.input('Mail', value=info.mail,
                    validation={'Adresse mail invalide': lambda v: not v or ('@' in v and '.' in v.split('@')[-1])}).props('type=email').classes('w-full')
                self.bic = required_label(ui.input('BIC', value=info.bic,
                    validation={'Champ obligatoire': lambda v: bool(v and v.strip()), 'BIC invalide': lambda v: not v or re.fullmatch(r'[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?', v) is not None}).props('maxlength=11 input-class=uppercase').classes('w-full'),"BIC")
                self.iban = required_label(ui.input('IBAN', value=info.iban,
                    validation={'Champ obligatoire': lambda v: bool(v and v.strip()), 'IBAN invalide': lambda v: not v or is_valid_iban(v)}).props('maxlength=42').classes('w-full'), "IBAN")
                ui.button('Valider', icon='check', on_click=self.validate)

    async def validate(self):
        required_fields = [self.name, self.addressee, self.street, self.zip_code, self.town, self.bic, self.iban]  # ajoutez street, zip_code, town, email, iban...
        if not all([f.validate() for f in required_fields]):
            ui.notify('Veuillez corriger les champs en erreur', type='negative')
            return

        self.promotion.information = Information(name=self.name.value, 
                           addressee=self.addressee.value,
                           street=self.street.value,
                           bp = self.bp.value,
                           zip = self.zip_code.value,
                           city=self.town.value,
                           phone=self.phone.value,
                           mail=self.email.value,
                           bic=self.bic.value,
                           iban=self.iban.value)
        database_controller.save_promotion(self.promotion)
        ui.notify(f"Informations mises à jour pour la promotion {self.promotion.year}", type='positive')


