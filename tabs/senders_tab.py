from dataclasses import fields
import json
from nicegui import ui
from controller.database_controller import database_controller
from model.model import Sender
from model.session_state import SessionState
from tabs.abstract_person_tab import AbstractPersonsTab


class SendersTab(AbstractPersonsTab):

    def __init__(self, session_state:SessionState, on_show_participants=None):
        self._on_show_participants = on_show_participants
        super().__init__(session_state, database_controller.notify_senders_changed)
        self.grille.on('cellClicked', self._on_cell_clicked)

    async def _handle_upload(self, e):
        await super()._handle_upload(e)
        await self.refresh_counts()

    def _get_empty_line(self):
        return {
            'title': '', 'name': '', 'firstname': '', 'street': '', 'zip': '',
            'city': '', 'phone': '', 'mail': '', 'organisation': '',
        }

    def _get_columns_def(self) -> list:
        return [
                {'headerName': 'Titre', 'width': 75, 'field': 'title', 'editable': True},
                {'headerName': 'Prénom', 'width': 150, 'field': 'firstname', 'editable': True},
                {'headerName': 'Nom', 'width': 150,'field': 'name', 'editable': True, ':valueParser': "params => (params.newValue ?? '').toString().toUpperCase()", 'cellClass': 'majuscules'},
                {'headerName': 'Adresse', 'width': 400, 'field': 'street', 'editable': True, 'autoHeight': True, 'cellStyle': {'whiteSpace': 'pre-line'}},
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
                {'headerName': 'Organisation', 'width': 400, 'field': 'organisation', 'editable': True},
                {'headerName': 'Participants', 'width': 130, 'field': 'nb_participants',
                'editable': False, 'sortable': True,
                'cellClass': 'text-center', 'headerClass': 'ag-center-header',
                ':cellRenderer': """params => {
                    const n = Number(params.value ?? 0);
                    if (!n) return '<span class="nb-chip-zero">–</span>';
                    return `<span class="nb-chip" title="Voir les participants">${n}</span>`;
                }"""},
            ]
    
    def _insert(self, line: dict) -> int:
        return database_controller.add_sender(line)

    def _update(self, line: dict):
        database_controller.update_sender(line)

    def _delete(self, ids: set[int]):
        database_controller.delete_senders(ids)    

    def _get_row_data(self):
        senders = database_controller.get_senders()
        lines = self._grid_lines(senders)
        counts = self._participants_per_sender()
        for line, sender in zip(lines, senders):
            line['nb_participants'] = counts.get(sender.label.lower(), 0)
        return lines

    def _get_required_fields(self) -> set[str]:
        return {'street', 'zip', 'city'}

    def _build_columns(self) -> list:
        columns = super()._build_columns()

        def filled(f: str) -> str:
            return f"(data['{f}'] ?? '').toString().trim()"

        editable = [c['field'] for c in columns if c.get('editable') and c.get('field')]
        row_not_empty = f"{json.dumps(editable)}.some(f => {filled('f').replace(chr(39) + 'f' + chr(39), 'f')})"
        invalid = (f"{row_not_empty} && !{filled('organisation')} "
                   f"&& !({filled('name')} && {filled('firstname')})")

        for col in columns:
            field = col.get('field')
            if field == 'organisation':
                rule = invalid
            elif field in ('name', 'firstname'):
                rule = f"!{filled(field)} && {invalid}"   # rouge seulement si le champ est vide
            else:
                continue
            col['cellClassRules'] = {**col.get('cellClassRules', {}), 'bg-red-300': rule}
        return columns        
    
    def _get_person_name(self) -> str:
        return "un envoyant"

    def _get_no_row_text(self):
        return "Aucun envoyant à afficher"

    def _get_import_tab_name(self):
        return "Envoyants"

    def _get_fields(self):
        return {f.name for f in fields(Sender)}

    def _participants_per_sender(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in self.session_state.promotion.participants if self.session_state.promotion else []:
            label = getattr(p, 'sender_label', '') or ''
            if label:
                label = label.lower()
                counts[label] = counts.get(label, 0) + 1
        return counts

    def _row_label(self, row: dict) -> str:
        sender = Sender(**{k: v for k, v in row.items() if k in self._get_fields()})
        return sender.label

    async def refresh_counts(self):
        """Recalcule la colonne « Participants » à partir des données enregistrées."""
        rows = self._get_row_data()
        self.grille.options['rowData'] = rows
        await self.grille.run_grid_method('setGridOption', 'rowData', rows)

    async def _on_cell_clicked(self, e):
        if e.args.get('colId') != 'nb_participants' or not e.args.get('value'):
            return
        row = e.args.get('data') or {}
        if self._on_show_participants:
            self._on_show_participants(self._row_label(row))
