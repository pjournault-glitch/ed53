from dataclasses import asdict
import json
import logging
import os
import uuid
from nicegui import ui, run
import io
from openpyxl import load_workbook

logger = logging.getLogger('app')

class AbstractPersonsTab:
    def __init__(self):
        self._upload = ui.upload(auto_upload=True,max_files=1,
            on_begin_upload=lambda e: self._set_buttons_enabled(False),
            on_upload=self._handle_upload).props('accept=.xlsx,.xlsm').classes('hidden')
        self._upload.on('failed', lambda e: (self._upload.reset(), self._set_buttons_enabled(True)))
        with ui.dialog().props('persistent') as self._busy_dialog, ui.card().classes('items-center gap-4 p-8'):
            ui.spinner(size='xl')
            self._busy_label = ui.label("Import en cours…")        
        self.grille = ui.aggrid({'rowSelection': {'mode': 'multiRow', 'checkboxes': True, 'headerCheckbox': True, 'enableClickSelection': False},
            'defaultColDef': {'resizable': True, 'sortable': True, 'width': 100},
            'columnDefs': self._build_columns(),
            'rowData': self._get_row_data(),
            "localeText": {"noRowsToShow": self._get_no_row_text()},
            ':getRowId': 'params => String(params.data.id)',
            'stopEditingWhenCellsLoseFocus': True,
            'singleClickEdit': True,
            ':onCellValueChanged': 'params => params.api.refreshCells({rowNodes: [params.node], force: true})',
            ':onFirstDataRendered': 'params => params.api.autoSizeAllColumns()',
            ':onGridSizeChanged': """params => {
                if (params.clientWidth > 0 && !params.api.__sized) {
                    params.api.__sized = true;
                    setTimeout(() => params.api.autoSizeAllColumns(), 50);
                }
            }""",
        }, auto_size_columns=True).classes('w-full grow min-h-[200px]')
        self.grille.on('cellValueChanged', self._save)
        self.grille.on('modelUpdated', self._update_count, args=['type'])
        self.grille.on('cellValueChanged', self._update_count, args=['type'])
        self.grille.on('firstDataRendered', self._update_count)     
        with ui.row().classes('w-full items-center justify-between no-wrap'):
            with ui.row():
                self._btn_add = ui.button(f"Ajouter une ligne", on_click=self._add_line, icon='person_add')
                if os.getenv("SHOW_IMPORT").lower() == "yes":
                    self._btn_import = ui.button("Importer un fichier excel", on_click=lambda: self._upload.run_method('pickFiles'), icon='upload_file')
                self._btn_remove = ui.button('Supprimer la sélection', on_click=self._remove_selection, color='negative', icon='delete')
                ui.button(icon='sym_o_fit_width', on_click=lambda: self.grille.run_grid_method('autoSizeAllColumns')).props('flat round dense').tooltip('Ajuster la largeur des colonnes')
                ui.button(icon='sym_o_refresh', on_click=self._reload).props('flat round dense').tooltip('Recharger les données')
            self._count_label = ui.label().classes('text-grey-7')
        self._update_count_local()
        self._notifier = None

    async def _reload(self):
        try:
            rows = self._get_row_data()
            self.grille.options['rowData'] = rows             # copie serveur à jour
            self.grille.run_grid_method('setGridOption', 'rowData', rows)
            await self._update_count()
            ui.notify('Données rechargées', type='positive')
        except Exception as ex:
            logger.exception('Rechargement impossible')
            ui.notify(f'Rechargement impossible : {ex}', type='negative')        

    def _editable_fields(self) -> list[str]:
        return [c['field'] for c in self.grille.options['columnDefs']
                if c.get('editable') and c.get('field')]

    def _show_count(self, shown: int, total: int) -> None:
        def lines(n: int) -> str:
            return f"{n} ligne{'s' if n > 1 else ''}"
        self._count_label.text = lines(total) if shown == total else f"{shown} / {lines(total)}"

    def _update_count_local(self) -> None:
        """Compte immédiat à partir des données connues côté serveur (sans filtre)."""
        fields = self._editable_fields()
        total = sum(1 for r in self.grille.options['rowData']
                    if any(str(r.get(f) or '').strip() for f in fields))
        self._show_count(total, total)
        # le navigateur corrige ensuite, au cas où un filtre est actif
        ui.timer(0.3, self._update_count, once=True)

    async def _update_count(self, _=None) -> None:
        try:
            await self.grille.client.connected()       # attend que le navigateur soit prêt
            shown, total = await self.grille.run_grid_method(self._count_js(), timeout=3)
        except Exception as ex:
            print(f'Compteur de lignes : {ex}')         # plus d'échec silencieux
            return
        self._show_count(shown, total)                  

    def _count_script(self) -> str:
        fields = json.dumps(self._editable_fields())
        return f"""
            const el = getElement({self.grille.id});
            const api = el && (el.api || el.gridApi);
            if (!api) return null;
            const fields = {fields};
            const filled = d => fields.some(k => (d[k] ?? '').toString().trim());
            let total = 0, shown = 0;
            api.forEachNode(n => {{ if (n.data && filled(n.data)) total++; }});
            api.forEachNodeAfterFilter(n => {{ if (n.data && filled(n.data)) shown++; }});
            return [shown, total];
        """

    async def _update_count(self, _=None) -> None:
        try:
            await self.grille.client.connected()       # attend que le navigateur soit prêt
            result = await self.grille.client.run_javascript(self._count_script(), timeout=3)
        except Exception as ex:
            print(f'Compteur de lignes : {ex}')
            return
        if not result:                                  # grille pas encore initialisée
            return
        shown, total = result
        self._show_count(shown, total)

    def _build_columns(self) -> list:
        columns = self._get_columns_def()
        required = self._get_required_fields()
        editable = [c['field'] for c in columns if c.get('editable') and c.get('field')]
        fields_js = json.dumps(editable)
        # rouge si la cellule est vide alors qu'un autre champ de la ligne est renseigné
        rule = ("!(x ?? '').toString().trim() && "
                f"{fields_js}.some(f => (data[f] ?? '').toString().trim())")
        for col in columns:
            if col.get('field') in required:
                col['cellClassRules'] = {**col.get('cellClassRules', {}), 'bg-red-300': rule}
        return columns

    def _insert(self, line: dict) -> int:
        raise NotImplementedError("La méthode _insert doit être implémentée dans la classe fille")   

    def _update(self, line: dict):
        raise NotImplementedError("La méthode _update doit être implémentée dans la classe fille")   

    def _delete(self, ids: set[int]):
        raise NotImplementedError("La méthode _delete doit être implémentée dans la classe fille")   
    
    def _get_required_fields(self) -> set[str]:
        raise NotImplementedError("La méthode _get_required_fields doit être implémentée dans la classe fille")   
    
    def _get_person_name(self) -> str:
        raise NotImplementedError("La méthode _get_person_name doit être implémentée dans la classe fille")   

    def _get_empty_line(self) -> dict:
        raise NotImplementedError("La méthode _get_empty_lines doit être implémentée dans la classe fille")   

    def _get_columns_def(self) -> list:
        raise NotImplementedError("La méthode _get_columns_def doit être implémentée dans la classe fille")   

    def _get_row_data(self):
        raise NotImplementedError("La méthode _get_row_data doit être implémentée dans la classe fille")

    def _get_no_row_text(self) -> str:
        raise NotImplementedError("La méthode _get_row_data doit être implémentée dans la classe fille")

    def _get_import_tab_name(self) -> str:
        raise NotImplementedError("La méthode _get_import_tab_name doit être implémentée dans la classe fille")
    
    def _get_fields(self):
        raise NotImplementedError("La méthode _get_fields doit être implémentée dans la classe fille")

    def _get_import_mapping(self) -> dict[str, str]:
        return dict(item.split(":", 1) for item in os.getenv("IMPORT_MAPPING").split(","))

    def _set_buttons_enabled(self, enabled: bool):
        for b in (self._btn_add, self._btn_import, self._btn_remove):
            b.set_enabled(enabled)

    def autosize_columns(self):
        ui.timer(0.2, lambda: self.grille.run_grid_method('autoSizeAllColumns'), once=True)            

    async def _handle_upload(self, e):
        self._set_buttons_enabled(False)
        try:
            data = await e.file.read() if hasattr(e, 'file') else e.content.read()
            lines, ignored = await run.io_bound(self._parse_excel, data)

            if not lines:
                ui.notify("Aucune ligne importée : en-têtes non reconnus ou fichier vide", type='warning')
                return

            # Insertion en base : chaque ligne reçoit l'id généré par la base
            def insert_all():
                for line in lines:
                    line['id'] = self._insert(line)

            await run.io_bound(insert_all)
            self._notifier(self.session_state.session_id, 'add', lines)

            # Ajout des nouvelles lignes à la grille, sans toucher aux existantes
            self.grille.run_grid_method('applyTransaction', {'add': lines})
            self.grille.run_grid_method('autoSizeAllColumns')

            msg = f"{len(lines)} ligne(s) importée(s)"
            if ignored:
                msg += f" (colonnes ignorées : {', '.join(ignored)})"
            ui.notify(msg, type='positive')
        except Exception as ex:
            ui.notify(f"Erreur à l'import : {ex}", type='negative')
        finally:
            self._upload.reset()
            self._set_buttons_enabled(True)
    
    def _parse_excel(self, data: bytes) -> tuple[list[dict], list[str]]:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb[self._get_import_tab_name()]
        rows = ws.iter_rows(min_row=1 + int(os.getenv("IMPORT_HEADER_LINES")), values_only=True)
        headers = next(rows, None)
        if not headers:
            return [], []

        mapping = self._get_import_mapping()
        col_to_field: dict[int, str] = {}
        ignored = []
        for i, h in enumerate(headers):
            key = str(h).strip().lower() if h is not None else ''
            if key in mapping:
                col_to_field[i] = mapping[key]
            elif key:
                ignored.append(str(h))

        lines = []
        for row in rows:
            line = self._get_empty_line()
            for i, field in col_to_field.items():
                if i < len(row) and row[i] is not None:
                    line[field] = str(row[i]).strip()
            if any(line.get(f) for f in col_to_field.values()):  # saute les lignes vides
                lines.append(line)
        return lines, ignored

    def _grid_lines(self, persons) -> list[dict]:
        lines = []
        for p in (persons or []):
            line = asdict(p)
            if line.get('id') is None:
                line['id'] = f"tmp-{uuid.uuid4().hex}"
            lines.append(line)
        return lines     

    async def _add_line(self):
        line = {**self._get_empty_line()}
        line['id'] = self._insert(line)               # id fourni par la base
        self._notifier(self.session_state.session_id, 'add', [line])
        self.grille.run_grid_method('applyTransaction', {'add': [line]})

    @staticmethod
    def _label(row: dict) -> str:
        return f"{row.get('firstname', '')} {row.get('name', '')}".strip()

    async def _confirm(self, message: str, confirm_label: str = 'Supprimer') -> bool:
        with ui.dialog() as dialog, ui.card():
            ui.label(message)
            with ui.row().classes('w-full justify-end'):
                ui.button('Annuler', on_click=lambda: dialog.submit(False)).props('flat')
                ui.button(confirm_label, color='negative', on_click=lambda: dialog.submit(True))
        result = await dialog
        dialog.delete()   # évite d'accumuler des dialogues dans la page
        return bool(result)
    
    async def _remove_selection(self):
        selection = await self.grille.get_selected_rows()
        if not selection:
            ui.notify('Aucune ligne sélectionnée', type='warning')
            return

        if len(selection) == 1:
            nom = self._label(selection[0]) or 'cette ligne'
            message = f"Supprimer « {nom} » ?"
        else:
            message = f"Supprimer les {len(selection)} lignes sélectionnées ?"

        if not await self._confirm(message):
            return

        ids = {r['id'] for r in selection}
        self._delete(ids)
        self._notifier(self.session_state.session_id, 'delete', selection)
        lines = await self.grille.get_client_data()
        self.grille.options['rowData'] = [l for l in lines if l['id'] not in ids]
        self.grille.update()
        ui.notify(f'{len(selection)} ligne(s) supprimée(s)')


    def apply_remote_change(self, op, payload):
        if op == 'add':
            self.grille.run_grid_method('applyTransaction', {'add': payload})
        elif op == 'update':
            self.grille.run_grid_method('applyTransaction', {'update': payload})
        elif op == 'delete':
            self.grille.run_grid_method('applyTransaction', {'remove': payload})        

    async def _save(self, e):
        line = e.args['data']
        self._update(line)
        self._notifier(self.session_state.session_id, 'update', [line])
