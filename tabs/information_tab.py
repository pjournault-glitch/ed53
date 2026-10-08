import re
from nicegui import run, ui
from controller.database_controller import database_controller
from model.model import Information
from util.util import required_label, required_rule


def is_valid_iban(value: str) -> bool:
    iban = value.replace(' ', '').upper()
    if not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]{11,30}', iban):
        return False
    rearranged = iban[4:] + iban[:4]
    digits = ''.join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


class InformationTab:
    def __init__(self):
        with ui.row().classes('w-full no-wrap gap-8'):
            with ui.column():
                self.name = required_label(ui.input('Nom', validation=required_rule).classes('w-full'), 'Nom')
                self.addressee = required_label(ui.input("À l'attention de", validation=required_rule).classes('w-full'), "À l'attention de")
                self.street = required_label(ui.input('Rue', validation=required_rule).classes('w-full'), 'Rue')
                self.bp = ui.input('Boîte postale').classes('w-full')
                with ui.row().classes('w-full no-wrap'):
                    self.zip_code = required_label(ui.input('Code postal', validation=required_rule).props('mask=##### maxlength=5').classes('w-32'), 'Code postal')
                    self.town = required_label(ui.input('Ville', validation=required_rule).classes('grow'), 'Ville')
                self.phone = ui.input('Téléphone').props('type=tel mask="## ## ## ## ##"').classes('w-full')
                self.email = ui.input(
                    'Mail',
                    validation={'Adresse mail invalide': lambda v: not v or ('@' in v and '.' in v.split('@')[-1])},
                ).props('type=email').classes('w-full')
                self.bic = required_label(ui.input(
                    'BIC',
                    validation={
                        'Champ obligatoire': lambda v: bool(v and v.strip()),
                        'BIC invalide': lambda v: not v or re.fullmatch(r'[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?', v) is not None,
                    },
                ).props('maxlength=11 input-class=uppercase').classes('w-full'), 'BIC')
                self.iban = required_label(ui.input(
                    'IBAN',
                    validation={
                        'Champ obligatoire': lambda v: bool(v and v.strip()),
                        'IBAN invalide': lambda v: not v or is_valid_iban(v),
                    },
                ).props('maxlength=42').classes('w-full'), 'IBAN')

        # correspondance champ de l'interface -> attribut de Information
        self._mapping = [
            (self.name, 'name'), (self.addressee, 'addressee'),
            (self.street, 'street'), (self.bp, 'bp'),
            (self.zip_code, 'zip'), (self.town, 'city'),
            (self.phone, 'phone'), (self.email, 'mail'),
            (self.bic, 'bic'), (self.iban, 'iban'),
        ]
        self.reload()

        for field, _ in self._mapping:
            field.on('blur', lambda e, f=field: self.autosave(f))  

    async def autosave(self, field):
        # on ne valide que le champ quitté (pas de rouge sur les champs
        # que l'utilisateur n'a pas encore remplis)
        if not field.validate():
            return
        # on n'enregistre que si tous les champs obligatoires sont valides,
        # sans afficher d'erreur sur les autres
        if not self._is_complete():
            return
        await run.io_bound(database_controller.save_information, self._build_information())

    def _is_complete(self) -> bool:
        required = [self.name, self.addressee, self.street, self.zip_code,
                    self.town, self.email, self.bic, self.iban]
        return all(self._is_ok(f) for f in required)

    @staticmethod
    def _is_ok(field) -> bool:
        # évalue les règles de validation sans modifier l'affichage de l'erreur
        for rule in (field.validation or {}).values():
            if not rule(field.value):
                return False
        return True                  

    def reload(self):
        info = database_controller.load_information()
        for field, attr in self._mapping:
            field.value = getattr(info, attr, '') or ''
        for field, _ in self._mapping:
            field.error = None   # pas de messages rouges à l'ouverture

    def _build_information(self) -> Information:
        return Information(
            name=self.name.value,
            addressee=self.addressee.value,
            street=self.street.value,
            bp=self.bp.value,
            zip=self.zip_code.value,
            city=self.town.value,
            phone=self.phone.value,
            mail=self.email.value,
            bic=self.bic.value,
            iban=self.iban.value,
        )