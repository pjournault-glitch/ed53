from datetime import date
import os
from nicegui import ui
from controller.database_controller import database_controller
from model.model import Promotion
from util.util import required_label, required_rule


class PromotionTab:
    def __init__(self, promotion:Promotion):
        self.promotion = promotion
        self.current_promotion_year = promotion.year

        with ui.dialog() as self.dialogue, ui.card():
            ui.label('Créer une nouvelle promotion').classes('text-lg font-bold')
            current_year = date.today().year
            self.new_promotion_year = required_label(ui.select(
                list(range(current_year, current_year + 6)),
                label='Année de départ',
                value=int(self.current_promotion_year) + 2,
            ).classes('w-full'),"Année de départ")
            ui.label().bind_text_from(self.new_promotion_year, 'value', backward=lambda v: f'Année de fin : {int(v) + 2}' if v is not None else '')
            self.year_fee = required_label(ui.number('Tarif annuel', validation=required_rule, value=self.promotion.year_fee, min=0, step=0.50, format='%.2f', suffix='€').classes('w-full'),"Tarif annuel")
            with ui.row().classes('justify-end w-full'):
                ui.button('Annuler', on_click=self.dialogue.close).props('flat')
                ui.button('Créer', on_click=self.creer_promotion)        

        with ui.row().classes('w-full no-wrap gap-8'):
            with ui.column():
                self.display_current_promotion()
                ui.label('Voulez-vous créer une nouvelle promotion ?')
                with ui.row():
                    ui.button('Oui', on_click=self.ouvrir_dialogue)

    def ouvrir_dialogue(self):
        self.dialogue.open()

    def creer_promotion(self):
        required_fields = [self.new_promotion_year, self.year_fee]
        if not all([f.validate() for f in required_fields]):
            ui.notify('Veuillez corriger les champs en erreur', type='negative')
            return
        
        promotion = Promotion(self.new_promotion_year.value, self.year_fee.value, self.promotion.information)
        database_controller.save_promotion(promotion)
        self.current_promotion_year = self.new_promotion_year.value
        self.display_current_promotion.refresh()
        self.dialogue.close()
        ui.notify(f'Nouvelle promotion créée : {self.new_promotion_year.value}', type='positive')

    @ui.refreshable
    def display_current_promotion(self):
        ui.label(f"Promotion en cours : {self.current_promotion_year}").classes('text-lg font-bold')

"""    
    def save(self, data_file):
        data_file.parent.mkdir(parents=True, exist_ok=True)
        data = {'year': int(self.year.value), 'name': self.name.value}
        data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        ui.notify('Promotion créée', type='positive')
"""
