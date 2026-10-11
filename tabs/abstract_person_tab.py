from dataclasses import asdict
import json
import os
import uuid
from nicegui import ui, run
import io
from openpyxl import load_workbook


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
            ':getRowId': 'params => params.data.id',
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
        }, auto_size_columns=False).classes('w-full grow min-h-[200px]')
        self.grille.on('cellValueChanged', self._save)
        with ui.row():
            self._btn_add = ui.button(f"Ajouter {self._get_person_name()}", on_click=self._add_line, icon='person_add')
            self._btn_import = ui.button("Importer un fichier excel", on_click=lambda: self._upload.run_method('pickFiles'), icon='upload_file')
            self._btn_remove = ui.button('Supprimer la sélection', on_click=self._remove_selection, color='negative', icon='delete')

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

    def _new_ligne(self) -> dict:
        return {**self._get_empty_line(), 'id': uuid.uuid4().hex}

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

            current = await self.grille.get_client_data()
            kept = [l for l in current if any(str(v).strip() for k, v in l.items() if k != 'id' and v is not None)]
            self.grille.options['rowData'] = kept + lines
            self.grille.update()
            await self.grille.run_grid_method('autoSizeAllColumns')
            await self._save()

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
                lines.append({**line, 'id': uuid.uuid4().hex})
        return lines, ignored

    def _grid_lines(self, persons, nb_vides: int = 10) -> list[dict]:
        lines = [{**asdict(p), 'id': uuid.uuid4().hex} for p in (persons or [])]
        lines += [self._new_ligne() for _ in range(nb_vides)]
        return lines

    async def _add_line(self):
        self.grille.run_grid_method('applyTransaction', {'add': [self._new_ligne()]})

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
        lines = await self.grille.get_client_data()
        self.grille.options['rowData'] = [l for l in lines if l['id'] not in ids]
        self.grille.update()
        await self._save()
        ui.notify(f'{len(selection)} ligne(s) supprimée(s)')

    async def _save(self):
        raise NotImplementedError("La méthode _save doit être implémentée dans la classe fille")   
