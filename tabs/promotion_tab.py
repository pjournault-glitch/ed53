from datetime import date
from nicegui import ui
from controller.database_controller import database_controller
from model.model import Promotion
from util.util import required_label, required_rule


class PromotionTab:
    def __init__(self):
        self._create_new_dialog()
        self._display_header()
        ui.separator().classes('my-4')

        with ui.row().classes('w-full gap-4 items-stretch'):
            # Ouvrir une autre promotion
            with ui.card().classes('w-72'):
                ui.label('Ouvrir une autre promotion').classes('text-subtitle1 font-bold')
                self.choix = ui.select(database_controller.existing_promotions(), label='Promotion').classes('w-full')
                ui.space()
                ui.button('Ouvrir', icon='folder_open',
                        on_click=lambda: self._select_promotion(self.choix.value)
                        ).bind_enabled_from(self.choix, 'value', backward=bool)

            # Nouvelle promotion
            with ui.card().classes('w-72'):
                ui.label('Nouvelle promotion').classes('text-subtitle1 font-bold')
                ui.label('Elle deviendra la promotion en cours.').classes('text-grey')
                ui.space()
                ui.button('Créer…', icon='add', on_click=self.dialogue.open)

    def _refresh_choices(self):
        self.choix.set_options(database_controller.existing_promotions(), value=None)

    def _create_new_dialog(self):
        with ui.dialog() as self.dialogue, ui.card():
            ui.label('Créer une nouvelle promotion').classes('text-lg font-bold')
            current_year = date.today().year
            self.new_promotion_year = required_label(ui.number('Année de départ', 
                validation={'Champ obligatoire': lambda v: v is not None,
                            'Cette valeur existe déjà': lambda v: not database_controller.promotion_exists(v)}, 
                            value=current_year, min=current_year-2, step=1, format='%4d').classes('w-full'),"Année de départ")
            ui.label().bind_text_from(self.new_promotion_year, 'value', backward=lambda v: f'Année de fin : {int(v) + 2}' if v is not None else '')
            self.year_fee = required_label(ui.number('Tarif annuel', validation=required_rule, value=database_controller.promotion.year_fee, min=0, step=0.50, format='%.2f', suffix='€').classes('w-full'),"Tarif annuel")
            with ui.row().classes('justify-end w-full'):
                ui.button('Annuler', on_click=self.dialogue.close).props('flat')
                ui.button('Créer', on_click=self._create_new_promotion)        

    @ui.refreshable
    def _display_header(self):
        promotion = database_controller.promotion
        with ui.column().classes('gap-1'):
            with ui.row().classes('items-center gap-3'):
                if database_controller.get_latest_promotion() == promotion.year:
                    ui.label(f"Dernière promotion : {promotion}").classes('text-h5')
                    ui.badge('en cours', color='positive')
                else:
                    ui.label(f"Promotion : {promotion}").classes('text-h5')
                    ui.badge('précédente', color='warning')
                    ui.button('Revenir à la dernière promotion', icon='undo',
                            on_click=lambda: self._select_promotion(database_controller.get_latest_promotion())).props('flat')
            fee = f'{promotion.year_fee:.2f}'.replace('.', ',')
            ui.label(f'Tarif annuel : {fee} €').classes('text-subtitle1 text-grey-8')

    def _create_new_promotion(self):
        required_fields = [self.new_promotion_year, self.year_fee]
        if not all([f.validate() for f in required_fields]):
            ui.notify('Veuillez corriger les champs en erreur', type='negative')
            return

        promotion = Promotion(int(self.new_promotion_year.value), self.year_fee.value, None)
        database_controller.save_promotion(promotion)
        database_controller.promotion = promotion

        self._refresh_choices() 
        self.dialogue.close()
        self._display_header.refresh()
        ui.notify(f'Nouvelle promotion créée : {self.new_promotion_year.value}', type='positive')

    def _select_promotion(self, year):
        database_controller.promotion = database_controller.load_promotion(year)
        self._display_header.refresh()

