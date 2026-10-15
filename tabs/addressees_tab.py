from dataclasses import fields
from nicegui import run

from controller.database_controller import database_controller
from model.model import Addressee
from tabs.abstract_person_tab import AbstractPersonsTab
from model.session_state import SessionState


class AddresseesTab(AbstractPersonsTab):
    def __init__(self, session_state:SessionState):
        super().__init__()
        self.session_state = session_state
        self._notifier = database_controller.notify_addressees_changed

    def _get_empty_line(self):
        return {
            'title': '', 'name': '', 'firstname': '', 'street': '', 'zip': '',
            'city': '', 'phone': '', 'mail': ''}

    def _get_columns_def(self) -> list:
        return [
                {'headerName': 'Titre', 'width': 75, 'field': 'title', 'editable': True},
                {'headerName': 'Prénom', 'width': 150, 'field': 'firstname', 'editable': True},
                {'headerName': 'Nom', 'width': 150,'field': 'name', 'editable': True, ':valueParser': "params => (params.newValue ?? '').toString().toUpperCase()", 'cellClass': 'majuscules'},
                {'headerName': 'Adresse', 'width': 200, 'field': 'street', 'editable': True},
                {'headerName': 'Code Postal', 'width': 150, 'field': 'zip', 'editable': True},
                {'headerName': 'Ville', 'width': 200, 'field': 'city', 'editable': True, ':valueParser': "params => (params.newValue ?? '').toString().toUpperCase()", 'cellClass': 'majuscules'},
                {'headerName': 'Téléphone', 'width': 150, 'field': 'phone', 'editable': True,  
                 ':valueParser': r"""params => {
                                    const s = (params.newValue ?? '').toString().trim();
                                    let d = s.replace(/\D/g, '');
                                    if (/^(\+|00)33/.test(s)) d = '0' + d.replace(/^(00)?33/, '');
                                    return d.replace(/(\d{2})(?=\d)/g, '$1 ');
                                }""",
                'cellClassRules': {
                    'bg-red-200': r'x && !/^0\d( \d{2}){4}$/.test(x)',
                },},
                {'headerName': 'Mèl', 'width': 250, 'field': 'mail', 'editable': True, 'cellClassRules': {'bg-red-200': r'x && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(x)'}},
            ]

    def _insert(self, line: dict) -> int:
        return database_controller.add_addressee(line)

    def _update(self, line: dict):
        database_controller.update_addressee(line)

    def _delete(self, ids: set[int]):
        database_controller.delete_addressees(ids)      

    def _get_row_data(self):
        return self._grid_lines(database_controller.get_addressees())

    def _get_required_fields(self) -> set[str]:
        return {'firstname', 'name', 'street', 'zip', 'city'}        

    def _get_person_name(self) -> str:
        return "un destinataire"

    def _get_no_row_text(self):
        return "Aucun destinataire à afficher"

    def _get_import_tab_name(self):
        return "Destinataires"    

    def _get_fields(self):
        return {f.name for f in fields(Addressee)}
