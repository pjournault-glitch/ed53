import asyncio
from dataclasses import asdict, fields
import uuid
from nicegui import run
from nicegui import ui

from controller.database_controller import database_controller
from model.model import Participant

EMPTY_LINE = {
    'title': '', 'name': '', 'firstname': '', 'street': '', 'zip': '',
    'city': '', 'phone': '', 'mail': '', 'sender': '',
}

FIELDS = {f.name for f in fields(Participant)}

class ParticipantsTab:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.grille = ui.aggrid({
                'rowSelection': {
                'mode': 'multiRow',
                'checkboxes': True,
                'headerCheckbox': True,          # case « tout sélectionner » dans l'en-tête
                'enableClickSelection': False,   # seules les cases sélectionnent
            },
            'defaultColDef': {'resizable': True, 'sortable': True, 'width': 100},
            'columnDefs': [
                {'headerName': 'Titre', 'width': 75, 'field': 'title', 'editable': True, 'cellEditor': 'agSelectCellEditor',
                    'cellEditorParams': {'values': ['', 'M.', 'Mme', 'Père', 'don']},},
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
                {'headerName': 'Mèl', 'width': 200, 'field': 'mail', 'editable': True, 'cellClassRules': {'bg-red-200': r'x && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(x)'}},
                {'headerName': 'Envoyé par', 'width': 200, 'field': 'sender', 'editable': True},
            ],
            'rowData': self._grid_lines(database_controller.promotion.participants, 0),
            ':getRowId': 'params => params.data.id',
            'stopEditingWhenCellsLoseFocus': True,
            'singleClickEdit': True,
        }, auto_size_columns=False).classes('w-full grow min-h-[200px]')
        self.grille.on('cellValueChanged', self._save)
        with ui.row():
            ui.button('Ajouter un participant', on_click=self._add_line)
            ui.button('Supprimer la sélection', on_click=self._remove_selection, color='negative')

    def _new_ligne(self) -> dict:
        return {**EMPTY_LINE, 'id': uuid.uuid4().hex}

    def _grid_lines(self, participants, nb_vides: int = 10) -> list[dict]:
        lines = [{**asdict(p), 'id': uuid.uuid4().hex} for p in (participants or [])]
        lines += [self._new_ligne() for _ in range(nb_vides)]
        return lines

    async def _add_line(self):
        await self.grille.run_grid_method('applyTransaction', {'add': [self._new_ligne()]})

    async def _remove_selection(self):
        selection = await self.grille.get_selected_rows()
        if not selection:
            ui.notify('Aucune ligne sélectionnée', type='warning')
            return
        ids = {r['id'] for r in selection}
        lines = await self.grille.get_client_data()
        self.grille.options['rowData'] = [l for l in lines if l['id'] not in ids]
        self.grille.update()
        await self._save()
        ui.notify(f'{len(selection)} ligne(s) supprimée(s)')

    async def _save(self):
        async with self._lock:
            lines = await self.grille.get_client_data()
        database_controller.promotion.participants = [
            Participant(**{k: v for k, v in l.items() if k in FIELDS})
            for l in lines
            if any(str(l.get(c) or '').strip() for c in FIELDS)
        ]
        await run.io_bound(
            database_controller.save_promotion,
            database_controller.promotion,
        )
