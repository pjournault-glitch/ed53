from dataclasses import fields
import json
import unicodedata
from nicegui import ui

from controller.database_controller import database_controller
from model.model import Participant
from tabs.abstract_person_tab import AbstractPersonsTab

SENDER_SETTER = """params => {
    const label = params.newValue ?? '';
    params.data.sender_label = label;
    return true;
}"""

def _cle_tri(texte: str) -> str:
    sans_accents = unicodedata.normalize('NFD', texte)
    return ''.join(c for c in sans_accents if unicodedata.category(c) != 'Mn').casefold()

class ParticipantsTab(AbstractPersonsTab):
    def __init__(self):
        database_controller.subscribe_promotion_changed(self.reload)
        database_controller.subscribe_senders_changed(self.reload)
        with ui.row().classes('w-full items-center justify-between no-wrap'):
            self._filter_sender = ui.select(
                options=self._sender_choices(),
                label='Filtrer par envoyant',
                clearable=True,
                on_change=self._apply_sender_filter,
            ).classes('w-128')
            self._promotion_label = ui.label(self._promotion_text()).classes('text-subtitle1 text-bold')            
        super().__init__()

    @staticmethod
    def _promotion_text() -> str:
        year = database_controller.promotion_year
        return f'Promotion ({year}-{year + 2})' if year else ''        

    def _get_empty_line(self):
        return {
            'title': '', 'name': '', 'firstname': '', 'street': '', 'zip': '',
            'city': '', 'phone': '', 'mail': '', 'sender_id': '', 'sender_label': '',
        }

    def _get_columns_def(self) -> list:
        return [
                {'headerName': 'Titre', 'width': 65, 'field': 'title', 'editable': True},
                {'headerName': 'Prénom', 'width': 130, 'field': 'firstname', 'editable': True},
                {'headerName': 'Nom', 'width': 130,'field': 'name', 'editable': True, ':valueParser': "params => (params.newValue ?? '').toString().toUpperCase()", 'cellClass': 'majuscules'},
                {'headerName': 'Adresse', 'width': 200, 'field': 'street', 'editable': True},
                {'headerName': 'Code Postal', 'width': 130, 'field': 'zip', 'editable': True},
                {'headerName': 'Ville', 'width': 200, 'field': 'city', 'editable': True, ':valueParser': "params => (params.newValue ?? '').toString().toUpperCase()", 'cellClass': 'majuscules'},
                {'headerName': 'Téléphone', 'width': 130, 'field': 'phone', 'editable': True,  
                 ':valueParser': r"""params => {
                                    const s = (params.newValue ?? '').toString().trim();
                                    let d = s.replace(/\D/g, '');
                                    if (/^(\+|00)33/.test(s)) d = '0' + d.replace(/^(00)?33/, '');
                                    return d.replace(/(\d{2})(?=\d)/g, '$1 ');
                                }""",
                'cellClassRules': {
                    'bg-red-200': r'x && !/^0\d( \d{2}){4}$/.test(x)',
                },},
                {'headerName': 'Mèl', 'width': 180, 'field': 'mail', 'editable': True, 'cellClassRules': {'bg-red-200': r'x && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(x)'}},
                {'headerName': 'Envoyé par', 'width': 500, 'field': 'sender_label', 'editable': True,
                 'cellEditor': 'agSelectCellEditor',
                 'cellEditorParams': {'values': self._sender_choices()},
                 ':valueSetter': SENDER_SETTER, 'filter': 'agTextColumnFilter','cellClassRules': self._sender_class_rules()},
            ]

    def _get_row_data(self):
        return self._grid_lines(database_controller.promotion.participants, 0)

    def _get_required_fields(self) -> set[str]:
        return {'firstname', 'name', 'street', 'zip', 'city', 'phone'}    

    def _get_person_name(self) -> str:
        return "un participant"

    def _get_no_row_text(self):
        return "Aucun participant à afficher"

    def _get_import_tab_name(self):
        return "Participants"       

    def _get_fields(self):
        return {f.name for f in fields(Participant)}

    def _sender_choices(self) -> list[str]:
        return sorted((s.label for s in database_controller.senders), key=_cle_tri)

    def reload(self):
        choices = self._sender_choices()
        for col in self.grille.options['columnDefs']:
            if col.get('field') == 'sender_label':
                col['cellEditorParams'] = {'values': choices}
                col['cellClassRules'] = self._sender_class_rules()
        self._filter_sender.set_options(choices)
        if self._filter_sender.value not in choices:
            self._filter_sender.value = None
        self.grille.options['rowData'] = self._grid_lines(
            database_controller.promotion.participants
        )
        self._promotion_label.text = self._promotion_text()
        self.grille.update()

    def filter_by_sender(self, label: str):
        """Sélectionne un envoyant dans la liste, ce qui filtre la grille."""
        choices = self._sender_choices()
        self._filter_sender.set_options(choices)      # liste à jour avant de choisir
        if label in choices:
            self._filter_sender.set_value(label)      # déclenche _apply_sender_filter
        else:
            self._filter_sender.set_value(None)       # libellé inconnu : pas de filtre

    async def _save(self):
        lines = await self.grille.get_client_data()
        database_controller.promotion.participants = [
            Participant(**{k: v for k, v in l.items() if k in self._get_fields()})
            for l in lines
            if any(str(l.get(c) or '').strip() for c in self._get_fields())
        ]
        database_controller.save_promotion(database_controller.promotion)

    async def _apply_sender_filter(self, e):
        model = ({'filterType': 'text', 'type': 'equals', 'filter': e.value}
                 if e.value else None)
        await self.grille.run_grid_method('setColumnFilterModel', 'sender_label', model)
        await self.grille.run_grid_method('onFilterChanged')

    def _sender_class_rules(self) -> dict:
        valid = json.dumps(self._sender_choices(), ensure_ascii=False)
        # rouge si la cellule n'est pas vide et n'est pas dans la liste des libellés
        return {'bg-red-200': f'x && !{valid}.includes(x)'}        