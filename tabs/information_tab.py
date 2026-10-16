import re
from nicegui import run, ui
from controller.database_controller import database_controller
from model.model import Information, Tag
from util.util import required_label, required_rule
from util.logging import log_user_action
from model.session_state import SessionState


def is_valid_iban(value: str) -> bool:
    iban = value.replace(' ', '').upper()
    if not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]{11,30}', iban):
        return False
    rearranged = iban[4:] + iban[:4]
    digits = ''.join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297

class InformationTab:
    def __init__(self, session_state:SessionState):
        super().__init__()
        self.session_state = session_state
        self._notifier = database_controller.notify_information_changed
        with ui.card().props('flat bordered').classes('w-full p-6'):
            with ui.row().classes('w-full no-wrap gap-8'):
                with ui.column().classes('flex-1 min-w-0'):
                    self.name = required_label(ui.input('Nom', validation=required_rule).classes('w-full'), 'Nom')
                    self.addressee = required_label(ui.input("À l'attention de", validation=required_rule).classes('w-full'), "À l'attention de")
                    self.street = required_label(ui.input('Rue', validation=required_rule).classes('w-full'), 'Rue')
                    self.bp = ui.input('Boîte postale').classes('w-full')
                    with ui.row().classes('w-full no-wrap'):
                        self.zip_code = required_label(ui.input('Code postal', validation=required_rule).props('mask=##### maxlength=5').classes('w-32'), 'Code postal')
                        self.town = required_label(ui.input('Ville', validation=required_rule).classes('grow'), 'Ville')
                with ui.column().classes('flex-1 min-w-0'):
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
        with ui.card().props('flat bordered').classes('w-full p-6'):
            ui.label('Étiquettes de courrier').classes('text-subtitle1 text-bold')
            with ui.row().classes('w-full no-wrap gap-8'):
                with ui.column().classes('flex-1 min-w-0'):
                    self.mail_margin_top = required_label(ui.input('Marge haute (mm)', validation=required_rule).classes('w-full'), 'Marge haute (mm)')
                    self.mail_margin_bottom = required_label(ui.input('Marge basse (mm)', validation=required_rule).classes('w-full'), 'Marge basse (mm)')
                    self.mail_margin_left = required_label(ui.input('Marge gauche (mm)', validation=required_rule).classes('w-full'), 'Marge gauche (mm)')
                    self.mail_margin_right = required_label(ui.input('Marge droite (mm)', validation=required_rule).classes('w-full'), 'Marge droite (mm)')
                with ui.column().classes('flex-1 min-w-0'):
                    self.mail_nb_horizontal = required_label(ui.input("Nombre d'étiquette par ligne", validation=required_rule).classes('w-full'), "Nombre d'étiquette par ligne")
                    self.mail_nb_vertical = required_label(ui.input("Nombre de lignes d'étiquettes", validation=required_rule).classes('w-full'), "Nombre de lignes d'étiquettes")
                    ui.label("\n").classes('champ-calcule')
                    self.mail_label_width = ui.label().classes('champ-calcule')
                    self.mail_label_height = ui.label().classes('champ-calcule')
                for field in (self.mail_margin_top, self.mail_margin_bottom,
                    self.mail_margin_left, self.mail_margin_right,
                    self.mail_nb_horizontal, self.mail_nb_vertical):
                    field.on_value_change(self._update_mail_label_size)
                self._update_mail_label_size()
        with ui.card().props('flat bordered').classes('w-full p-6'):
            ui.label('Étiquettes de dossiers').classes('text-subtitle1 text-bold')
            with ui.row().classes('w-full no-wrap gap-8'):
                with ui.column().classes('flex-1 min-w-0'):
                    self.file_margin_top = required_label(ui.input('Marge haute (mm)', validation=required_rule).classes('w-full'), 'Marge haute (mm)')
                    self.file_margin_bottom = required_label(ui.input('Marge basse (mm)', validation=required_rule).classes('w-full'), 'Marge basse (mm)')
                    self.file_margin_left = required_label(ui.input('Marge gauche (mm)', validation=required_rule).classes('w-full'), 'Marge gauche (mm)')
                    self.file_margin_right = required_label(ui.input('Marge droite (mm)', validation=required_rule).classes('w-full'), 'Marge droite (mm)')
                with ui.column().classes('flex-1 min-w-0'):
                    self.file_nb_horizontal = required_label(ui.input("Nombre d'étiquette par ligne", validation=required_rule).classes('w-full'), "Nombre d'étiquette par ligne")
                    self.file_nb_vertical = required_label(ui.input("Nombre de lignes d'étiquettes", validation=required_rule).classes('w-full'), "Nombre de lignes d'étiquettes")
                    ui.label("\n").classes('champ-calcule')
                    self.file_label_width = ui.label().classes('champ-calcule')
                    self.file_label_height = ui.label().classes('champ-calcule')
                for field in (self.file_margin_top, self.file_margin_bottom,
                    self.file_margin_left, self.file_margin_right,
                    self.file_nb_horizontal, self.file_nb_vertical):
                    field.on_value_change(self._update_file_label_size)
                self._update_file_label_size()
        with ui.card().props('flat bordered').classes('w-full p-6'):
            ui.label('Badges').classes('text-subtitle1 text-bold')
            with ui.row().classes('w-full no-wrap gap-8'):
                with ui.column().classes('flex-1 min-w-0'):
                    self.badge_margin_top = required_label(ui.input('Marge haute (mm)', validation=required_rule).classes('w-full'), 'Marge haute (mm)')
                    self.badge_margin_bottom = required_label(ui.input('Marge basse (mm)', validation=required_rule).classes('w-full'), 'Marge basse (mm)')
                    self.badge_margin_left = required_label(ui.input('Marge gauche (mm)', validation=required_rule).classes('w-full'), 'Marge gauche (mm)')
                    self.badge_margin_right = required_label(ui.input('Marge droite (mm)', validation=required_rule).classes('w-full'), 'Marge droite (mm)')
                with ui.column().classes('flex-1 min-w-0'):
                    self.badge_nb_horizontal = required_label(ui.input("Nombre d'étiquette par ligne", validation=required_rule).classes('w-full'), "Nombre d'étiquette par ligne")
                    self.badge_nb_vertical = required_label(ui.input("Nombre de lignes d'étiquettes", validation=required_rule).classes('w-full'), "Nombre de lignes d'étiquettes")
                    ui.label("\n").classes('champ-calcule')
                    self.badge_label_width = ui.label().classes('champ-calcule')
                    self.badge_label_height = ui.label().classes('champ-calcule')
                for field in (self.badge_margin_top, self.badge_margin_bottom,
                    self.badge_margin_left, self.badge_margin_right,
                    self.badge_nb_horizontal, self.badge_nb_vertical):
                    field.on_value_change(self._update_badge_label_size)
                self._update_badge_label_size()

        # correspondance champ de l'interface -> attribut de Information
        self._mapping = [
            (self.name, 'name'), (self.addressee, 'addressee'),
            (self.street, 'street'), (self.bp, 'bp'),
            (self.zip_code, 'zip'), (self.town, 'city'),
            (self.phone, 'phone'), (self.email, 'mail'),
            (self.bic, 'bic'), (self.iban, 'iban'),
        ]
        self._mail_tag_mapping = [
            (self.mail_margin_top, 'margin_top', float),
            (self.mail_margin_bottom, 'margin_bottom', float),
            (self.mail_margin_left, 'margin_left', float),
            (self.mail_margin_right, 'margin_right', float),
            (self.mail_nb_horizontal, 'nb_horizontal', int),
            (self.mail_nb_vertical, 'nb_vertical', int),
        ]
        self._file_tag_mapping = [
            (self.file_margin_top, 'margin_top', float),
            (self.file_margin_bottom, 'margin_bottom', float),
            (self.file_margin_left, 'margin_left', float),
            (self.file_margin_right, 'margin_right', float),
            (self.file_nb_horizontal, 'nb_horizontal', int),
            (self.file_nb_vertical, 'nb_vertical', int),
        ]
        self._badge_tag_mapping = [
            (self.badge_margin_top, 'margin_top', float),
            (self.badge_margin_bottom, 'margin_bottom', float),
            (self.badge_margin_left, 'margin_left', float),
            (self.badge_margin_right, 'margin_right', float),
            (self.badge_nb_horizontal, 'nb_horizontal', int),
            (self.badge_nb_vertical, 'nb_vertical', int),
        ]        
        if not self.session_state.can_edit:
            for field, _ in self._mapping:
                field.set_enabled(False)
        self._info = None
        self.reload()
        self._focused = None                      # champ en cours de saisie dans cette session

        self._client = ui.context.client          # pour afficher les messages dans le bon navigateur
        database_controller.subscribe_information_changed(self._on_information_changed)        

        all_fields = [f for f, _ in self._mapping] + [f for f, _, _ in self._mail_tag_mapping] + [f for f, _, _ in self._file_tag_mapping]  + [f for f, _, _ in self._badge_tag_mapping]
        for field in all_fields:
            field.on('focus', lambda e, f=field: setattr(self, '_focused', f))
            field.on('blur', lambda e, f=field: self.autosave(f))

    def unsubscribe(self) -> None:
        database_controller.unsubscribe_information_changed(self._on_information_changed)

    def _on_information_changed(self, origin, op, payload):
        if origin == self.session_state.session_id:
            return
        self.reload(keep=self._focused)

    async def autosave(self, field):
        if self._focused is field:
            self._focused = None
        if not field.validate():
            return

        if not self.session_state.can_edit:
            for tag_name, mapping, build_tag in (
                ('mail_tag', self._mail_tag_mapping, self._build_mail_tag),
                ('file_tag', self._file_tag_mapping, self._build_file_tag),
                ('badge_tag', self._badge_tag_mapping, self._build_badge_tag),
            ):
                if any(tag_field is field for tag_field, _, _ in mapping):
                    if not all(self._is_ok(tag_field) and self._num(tag_field) is not None
                               for tag_field, _, _ in mapping):
                        return
                    await run.io_bound(database_controller.save_information_tag, tag_name, build_tag())
                    log_user_action(self.session_state.name, 'modification', tag_name)
                    self._notifier(self.session_state.session_id, 'update', None)
                    return
            return

        if not self._is_complete():
            return
        info = self._build_information()          # lecture de l'interface avant l'await
        await run.io_bound(database_controller.save_information, info)
        log_user_action(self.session_state.name, 'modification', 'informations générales')
        self._notifier(self.session_state.session_id, 'update', None)

    def _is_complete(self) -> bool:
        required = [self.name, self.addressee, self.street, self.zip_code,
                    self.town, self.email, self.bic, self.iban]
        if not all(self._is_ok(f) for f in required):
            return False
        # les champs de l'étiquette doivent être renseignés et numériques
        if not all(self._is_ok(f) and self._num(f) is not None
                   for f, _, _ in self._mail_tag_mapping):
            return False
        if not all(self._is_ok(f) and self._num(f) is not None
                   for f, _, _ in self._file_tag_mapping):
            return False
        return all(self._is_ok(f) and self._num(f) is not None
                   for f, _, _ in self._badge_tag_mapping)
    
    def _update_mail_label_size(self, _=None):
        left, right = self._num(self.mail_margin_left), self._num(self.mail_margin_right)
        top, bottom = self._num(self.mail_margin_top), self._num(self.mail_margin_bottom)
        nb_h, nb_v = self._num(self.mail_nb_horizontal), self._num(self.mail_nb_vertical)

        width = None
        if None not in (left, right, nb_h) and nb_h >= 1:
            width = (A4_WIDTH_MM - left - right) / int(nb_h)

        height = None
        if None not in (top, bottom, nb_v) and nb_v >= 1:
            height = (A4_HEIGHT_MM - top - bottom) / int(nb_v)

        self.mail_label_width.text = (
            f"Largeur d'une étiquette : {width:.1f} mm" if width and width > 0 else "Largeur d'une étiquette : —")
        self.mail_label_height.text = (
            f"Hauteur d'une étiquette : {height:.1f} mm" if height and height > 0 else "Hauteur d'une étiquette : —")    

    def _update_file_label_size(self, _=None):
        left, right = self._num(self.file_margin_left), self._num(self.file_margin_right)
        top, bottom = self._num(self.file_margin_top), self._num(self.file_margin_bottom)
        nb_h, nb_v = self._num(self.file_nb_horizontal), self._num(self.file_nb_vertical)

        width = None
        if None not in (left, right, nb_h) and nb_h >= 1:
            width = (A4_WIDTH_MM - left - right) / int(nb_h)

        height = None
        if None not in (top, bottom, nb_v) and nb_v >= 1:
            height = (A4_HEIGHT_MM - top - bottom) / int(nb_v)

        self.file_label_width.text = (
            f"Largeur d'une étiquette : {width:.1f} mm" if width and width > 0 else "Largeur d'une étiquette : —")
        self.file_label_height.text = (
            f"Hauteur d'une étiquette : {height:.1f} mm" if height and height > 0 else "Hauteur d'une étiquette : —")    

    def _update_badge_label_size(self, _=None):
        left, right = self._num(self.badge_margin_left), self._num(self.badge_margin_right)
        top, bottom = self._num(self.badge_margin_top), self._num(self.badge_margin_bottom)
        nb_h, nb_v = self._num(self.badge_nb_horizontal), self._num(self.badge_nb_vertical)

        width = None
        if None not in (left, right, nb_h) and nb_h >= 1:
            width = (A4_WIDTH_MM - left - right) / int(nb_h)

        height = None
        if None not in (top, bottom, nb_v) and nb_v >= 1:
            height = (A4_HEIGHT_MM - top - bottom) / int(nb_v)

        self.badge_label_width.text = (
            f"Largeur d'un badge : {width:.1f} mm" if width and width > 0 else "Largeur d'un badge : —")
        self.badge_label_height.text = (
            f"Hauteur d'un badge : {height:.1f} mm" if height and height > 0 else "Hauteur d'un badge : —")    

    @staticmethod
    def _num(field) -> float | None:
        # accepte la virgule décimale française ; renvoie None si vide ou invalide
        try:
            return float(str(field.value).replace(',', '.').strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_ok(field) -> bool:
        # évalue les règles de validation sans modifier l'affichage de l'erreur
        for rule in (field.validation or {}).values():
            if not rule(field.value):
                return False
        return True                  

    def reload(self, keep=None):
        self._info = database_controller.load_information()
        values = [(field, getattr(self._info, attr, '') or '') for field, attr in self._mapping]
        for tag_name, mapping in (('mail_tag', self._mail_tag_mapping),
                                ('file_tag', self._file_tag_mapping),
                                ('badge_tag', self._badge_tag_mapping)):
            tag = getattr(self._info, tag_name, None)
            for field, attr, _ in mapping:
                value = getattr(tag, attr, None) if tag else None
                values.append((field, '' if value is None else f'{value:g}'))
        for field, value in values:
            if field is keep:
                continue                           # ne pas écraser ce que l'utilisateur est en train de saisir
            field.value = value
            field.error = None

    def _build_mail_tag(self) -> Tag:
        values = {attr: kind(self._num(field))
                  for field, attr, kind in self._mail_tag_mapping}
        return Tag(**values)
    
    def _build_file_tag(self) -> Tag:
        values = {attr: kind(self._num(field))
                  for field, attr, kind in self._file_tag_mapping}
        return Tag(**values)

    def _build_badge_tag(self) -> Tag:
        values = {attr: kind(self._num(field))
                  for field, attr, kind in self._badge_tag_mapping}
        return Tag(**values)

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
            mail_tag=self._build_mail_tag(),
            file_tag=self._build_file_tag(),
            badge_tag=self._build_badge_tag(),
        )