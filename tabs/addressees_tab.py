from dataclasses import fields
from nicegui import run

from controller.database_controller import database_controller
from model.model import Addressee
from tabs.abstract_person_tab import AbstractPersonsTab


class AddresseesTab(AbstractPersonsTab):

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

    def _get_row_data(self):
        return self._grid_lines(database_controller.addressees, 0)

    def _get_person_name(self) -> str:
        return "un destinataire"

    def _get_no_row_text(self):
        return "Aucun destinataire à afficher"

    def _get_import_tab_name(self):
        return "Destinataires"    

    def _get_fields(self):
        return {f.name for f in fields(Addressee)}

    async def _save(self):
        lines = await self.grille.get_client_data()
        database_controller.addressees = [
            Addressee(**{k: v for k, v in l.items() if k in self._get_fields()})
            for l in lines
            if any(str(l.get(c) or '').strip() for c in self._get_fields())
        ]
        database_controller.save_addressees()
