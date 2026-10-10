import asyncio
from dataclasses import asdict, fields
import unicodedata
import uuid
from nicegui import run
from nicegui import ui

from controller.database_controller import database_controller
from model.model import Participant, Sender
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
        super().__init__()

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
                 ':valueSetter': SENDER_SETTER},
            ]

    def _get_row_data(self):
        return self._grid_lines(database_controller.promotion.participants, 0)

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
        """Recharge la grille : participants de la promotion en cours + liste des senders."""
        for col in self.grille.options['columnDefs']:
            if col.get('field') == 'sender_label':
                col['cellEditorParams'] = {'values': self._sender_choices()}
        self.grille.options['rowData'] = self._grid_lines(
            database_controller.promotion.participants
        )
        self.grille.update()

    async def _save(self):
        lines = await self.grille.get_client_data()
        database_controller.promotion.participants = [
            Participant(**{k: v for k, v in l.items() if k in self._get_fields()})
            for l in lines
            if any(str(l.get(c) or '').strip() for c in self._get_fields())
        ]
        database_controller.save_promotion(database_controller.promotion)