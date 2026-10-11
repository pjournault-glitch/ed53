import asyncio

from dotenv import load_dotenv
from nicegui import ui

from controller.database_controller import database_controller
from tabs.about_tab import AboutTab
from tabs.addressees_tab import AddresseesTab
from tabs.information_tab import InformationTab
from tabs.participants_tab import ParticipantsTab
from tabs.promotion_tab import PromotionTab
from tabs.senders_tab import SendersTab
from tabs.animators_tab import AnimatorsTab

class Main:
    def __init__(self):
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')
        ui.add_css('.majuscules, .majuscules input { text-transform: uppercase; }')
        ui.add_css('body { font-size: 12px; }', shared=True)
        ui.add_css('''.champ-calcule { font-size: 16px; line-height: 1.2; letter-spacing: .00937em; font-weight: 400; color: rgba(0, 0, 0, .6); }
                    .body--dark .champ-calcule { color: rgba(255, 255, 255, .7); }
                    ''')

        load_dotenv(override=True)
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
            etat = {'titre': 'Promotion'}
            with ui.tabs(on_change=self._on_tab_change).props('inline-label') as self.tabs:
                with ui.tab(name='promo', label=''):
                    ui.label().bind_text_from(database_controller, 'promotion_year', backward=lambda y: f'Promotion ({y} - {y+2})' if y else 'Promotion').style('font-size: 16px !important')
                self._tab_participants = ui.tab('participants', label='Participants').style('font-size: 18px !important')
                ui.tab('animators', label='Animateurs').style('font-size: 18px !important')
                ui.tab('addressees', label='Destinataires').style('font-size: 18px !important')
                self._tab_senders = ui.tab('senders', label='Envoyants').style('font-size: 18px !important')
                ui.tab('info', label='Informations Générales', icon='settings').style('font-size: 18px !important')
                ui.tab('apropos', label='A PROPOS', icon='info').style('font-size: 18px !important')

    def _show_participants(self, label: str):
        self.tabs.set_value(self._tab_participants)            # bascule sur l'onglet
        self._participants_tab.filter_by_sender(label)    # applique le filtre

    def _on_tab_change(self, e):
        if e.value == self._tab_senders:                  # recalcule les compteurs au retour
            asyncio.create_task(self._senders_tab.refresh_counts())

    def _build_tab_pages(self):
        with ui.tab_panels(self.tabs, value='promo').classes('w-full grow'):
            with ui.tab_panel('promo'):
                PromotionTab()
            with ui.tab_panel('info'):
                InformationTab()
            with ui.tab_panel('participants').classes('flex flex-col min-h-0'):
                self._participants_tab = ParticipantsTab()
            with ui.tab_panel('animators').classes('flex flex-col min-h-0'):
                AnimatorsTab()                
            with ui.tab_panel('addressees').classes('flex flex-col min-h-0'):
                AddresseesTab()                
            with ui.tab_panel('senders').classes('flex flex-col min-h-0'):
                self._senders_tab = SendersTab(on_show_participants=self._show_participants)                
            with ui.tab_panel('apropos'):
                AboutTab()                

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