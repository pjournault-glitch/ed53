from dotenv import load_dotenv
from nicegui import ui

from controller.database_controller import database_controller
from tabs.information_tab import InformationTab
from tabs.promotion_tab import PromotionTab

class Main:
    def __init__(self):
        load_dotenv()
        latest_promotion_file = database_controller.get_latest_promotion_file()
        self.promotion = database_controller.load_promotion(latest_promotion_file)
        self._build_left_drawer()
        self._build_tabs()
        self._build_tab_pages()

    def _build_left_drawer(self):
        with ui.left_drawer().classes('bg-blue-100') as self.left_drawer:
            with ui.list().props('padding'):
                ui.label("Générations")
                self._add_menu_item("sym_o_signature", "Feuilles d'émargement", self._generate_signatures)
                self._add_menu_item("sym_o_room_service", "Repas Année 1", lambda: self._generate_meals(1))
                self._add_menu_item("sym_o_room_service", "Repas Année 2", lambda: self._generate_meals(2))
                self._add_menu_item("sym_o_payments", "Factures Année 1", lambda: self._generate_invoices(1))
                self._add_menu_item("sym_o_payments", "Factures Année 2", lambda: self._generate_invoices(2))
                self._add_menu_item("sym_o_mail", "Etiquettes courriers", self._generate_mails)
                self._add_menu_item("sym_o_files", "Etiquettes dossiers", self._generate_files)
                self._add_menu_item("sym_o_badge", "Badges", self._generate_badges)

    def _build_tabs(self):
        with ui.header().classes(replace='row items-center') as header:
            ui.button(on_click=lambda: self.left_drawer.toggle(), icon='menu').props('flat color=white')
            with ui.tabs() as self.tabs:
                ui.tab('Promotion')
                ui.tab('Information')
                ui.tab('Participants')
                ui.tab('Animateurs')
                ui.tab('Destinataires')
                ui.tab('Envoyants')

    def _build_tab_pages(self):
        with ui.tab_panels(self.tabs, value='Promotion').classes('w-full'):
            with ui.tab_panel('Promotion'):
                promotion_tab = PromotionTab(self.promotion)
            with ui.tab_panel('Information'):
                information_tab = InformationTab(self.promotion)
            with ui.tab_panel('B'):
                ui.label('Content of B')
            with ui.tab_panel('C'):
                ui.label('Content of C')

    def _add_menu_item(self, icon_name, label, fonction):
        with ui.item(on_click=fonction):
            with ui.item_section().props('avatar'):
                ui.icon(icon_name)
            with ui.item_section():
                ui.item_label(label)

    def _generate_signatures(self):
        ui.notify("Emargement")

    def _generate_meals(self, year):
        ui.notify(f"Repas {year}")

    def _generate_invoices(self, year):
        ui.notify(f"Facture {year}")

    def _generate_mails(self):
        ui.notify("Courriers")

    def _generate_files(self):
        ui.notify("Dossiers")

    def _generate_badges(self):
        ui.notify("Badges")
    
    def run(self):
        ui.run(title='Ecole du diocèse')

Main().run()    