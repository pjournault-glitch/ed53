import asyncio
from dataclasses import asdict
import uuid
from nicegui import ui


class AbstractPersonsTab:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.grille = ui.aggrid({'rowSelection': {'mode': 'multiRow', 'checkboxes': True, 'headerCheckbox': True, 'enableClickSelection': False},
            'defaultColDef': {'resizable': True, 'sortable': True, 'width': 100},
            'columnDefs': self._get_columns_def(),
            'rowData': self._get_row_data(),
            "localeText": {"noRowsToShow": self._get_no_row_text()},
            ':getRowId': 'params => params.data.id',
            'stopEditingWhenCellsLoseFocus': True,
            'singleClickEdit': True,
        }, auto_size_columns=False).classes('w-full grow min-h-[200px]')
        self.grille.on('cellValueChanged', self._save)
        with ui.row():
            ui.button(f"Ajouter {self._get_person_name()}", on_click=self._add_line)
            ui.button('Supprimer la sélection', on_click=self._remove_selection, color='negative')

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

    def _get_fields(self):
        raise NotImplementedError("La méthode _get_fields doit être implémentée dans la classe fille")

    def _new_ligne(self) -> dict:
        return {**self._get_empty_line(), 'id': uuid.uuid4().hex}

    def _grid_lines(self, persons, nb_vides: int = 10) -> list[dict]:
        lines = [{**asdict(p), 'id': uuid.uuid4().hex} for p in (persons or [])]
        lines += [self._new_ligne() for _ in range(nb_vides)]
        return lines

    async def _add_line(self):
        self.grille.run_grid_method('applyTransaction', {'add': [self._new_ligne()]})

    @staticmethod
    def _label(row: dict) -> str:
        return f"{row.get('firstname', '')} {row.get('name', '')}".strip()
    
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
        raise NotImplementedError("La méthode _save doit être implémentée dans la classe fille")   
