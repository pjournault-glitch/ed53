import asyncio
from datetime import datetime
import os

from dotenv import load_dotenv
from nicegui import ui

from controller.database_controller import database_controller
from controller.file_label_controller import FileLabelController
from controller.meal_controller import MealController
from tabs.about_tab import AboutTab
from tabs.addressees_tab import AddresseesTab
from tabs.information_tab import InformationTab
from tabs.participants_tab import ParticipantsTab
from tabs.promotion_tab import PromotionTab
from tabs.senders_tab import SendersTab
from tabs.animators_tab import AnimatorsTab
from controller.attendance_controller import AttendanceController
from controller.mail_label_controller import MailLabelController
from model.model import Addressee

def _required(v) -> bool:
    return bool(v and v.strip())

def _valid_date(v) -> bool:
    try:
        datetime.strptime(v or '', '%d/%m/%Y')
        return True
    except ValueError:
        return False

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
                self._add_menu_item("sym_o_signature", "Feuilles d'émargement Année 1", lambda: self._generate_attendance(1))
                self._add_menu_item("sym_o_signature", "Feuilles d'émargement Année 2", lambda: self._generate_attendance(2))
                self._add_menu_item("sym_o_room_service", "Repas Année 1", lambda: self._generate_meal(1))
                self._add_menu_item("sym_o_room_service", "Repas Année 2", lambda: self._generate_meal(2))
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

    def _generate_attendance(self, year):
        promotion = database_controller.promotion
        information = database_controller.load_information()
        pdf = AttendanceController(promotion.participants, "Feuille d'émargement",
            f"{information.name} {promotion.year}-{promotion.year + 2} - Années {promotion.year + year-1}-{promotion.year + year}",
            int(os.getenv("ATTENDANCE_FROM")), int(os.getenv("ATTENDANCE_TO"))).generate()
        ui.download(pdf, f"emargement_{promotion.year + year-1}_{promotion.year + year}.pdf")

    def _generate_meal(self, year):
        promotion = database_controller.promotion
        information = database_controller.load_information()
        pdf = MealController(promotion.participants, "Règlement des repas",
            f"{information.name} {promotion.year}-{promotion.year + 2} - Années {promotion.year + year-1}-{promotion.year + year}").generate()
        ui.download(pdf, f"repas_{promotion.year + year-1}_{promotion.year + year}.pdf")

    def _generate_invoices(self, year):
        ui.notify(f"Facture {year}")

    def _generate_mails(self):
        promotion = database_controller.promotion
        persons = sorted(promotion.participants + database_controller.addressees, key=lambda p: p.name)
        information = database_controller.load_information()
        pdf = MailLabelController(persons, information.mail_tag).generate()
        ui.download(pdf, f"courrier_{promotion.year}_{promotion.year + 2}.pdf")

    async def ask_intervention(self) -> dict | None:
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label("Détail de l'intervention").classes('text-lg font-bold')

            speaker = ui.input("Nom de l'intervenant",
                            validation={'Champ obligatoire': _required}).classes('w-full')
            title = ui.input("Titre de l'intervention",
                            validation={'Champ obligatoire': _required}).classes('w-full')

            # date : saisie au clavier (JJ/MM/AAAA) ou choix dans un calendrier
            with ui.input("Date de l'intervention",
                        validation={'Date invalide (JJ/MM/AAAA)': _valid_date}).classes('w-full') as date_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date(mask='DD/MM/YYYY').bind_value(date_input):
                        with ui.row().classes('justify-end'):
                            ui.button('Fermer', on_click=menu.close).props('flat')
                with date_input.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            def validate():
                # liste (et non générateur) : tous les champs sont validés, pour afficher toutes les erreurs
                if all([f.validate() for f in (speaker, title, date_input)]):
                    dialog.submit({
                        'speaker': speaker.value.strip(),
                        'title': title.value.strip(),
                        'date': datetime.strptime(date_input.value, '%d/%m/%Y').date(),
                    })

            with ui.row().classes('w-full justify-end'):
                ui.button('Annuler', on_click=lambda: dialog.submit(None)).props('flat')
                ui.button('Valider', on_click=validate)

        result = await dialog
        dialog.delete()   # évite d'accumuler des dialogues dans la page
        return result        

    async def _generate_files(self):
        intervention = await self.ask_intervention()
        if intervention is None:
            return
        promotion = database_controller.promotion
        persons = promotion.participants + database_controller.animators
        information = database_controller.load_information()
        pdf = FileLabelController(persons, intervention, information.file_tag, extra_identities=('INTERVENANT', 'ARCHIVE')).generate()
        ui.download(pdf, f"dossier_{promotion.year}_{promotion.year + 2}.pdf")

    def _generate_badges(self):
        ui.notify("Badges")
    
    def run(self):
        ui.run(title='Ecole du diocèse')

Main().run()    