import logging
import os
from util.util import required, to_display, valid_date
from nicegui import ui
from controller.database_controller import database_controller
from datetime import datetime
from functools import partial
from nicegui import ui

from controller.badge_controller import BadgeController
from controller.database_controller import database_controller
from controller.export_excel_controller import ExportExcelController
from controller.file_label_controller import FileLabelController
from controller.invoice_controller import InvoiceController
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
from model.session_state import SessionState

logger = logging.getLogger('app')

class MainWindow:
    def __init__(self, session_state:SessionState):
        self.session_state = session_state
        self._build_header_and_css()        
        self._build_drawer()
        self._build_tabs()
        self._build_tab_pages()
        self._subscribe_changes()
        self.last_speaker = None
        self.last_title = None
        self.last_intervention_date = None
        # ui.context.client.on_disconnect(self._unsubscribe_changes)

    def _build_header_and_css(self):
        """Construit le header et les css HTML"""
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')
        ui.add_css('.majuscules, .majuscules input { text-transform: uppercase; }')
        ui.add_css('body { font-size: 12px; }', shared=True)
        ui.add_css('''.champ-calcule { font-size: 16px; line-height: 1.2; letter-spacing: .00937em; font-weight: 400; color: rgba(0, 0, 0, .6); }
                    .body--dark .champ-calcule { color: rgba(255, 255, 255, .7); }
                    ''')
        ui.add_head_html("""
                            <script>
                            window.addEventListener('error', e => emitEvent('js_error',
                                {message: e.message, source: e.filename, line: e.lineno}));
                            window.addEventListener('unhandledrejection', e => emitEvent('js_error',
                                {message: String(e.reason), source: 'promise', line: 0}));
                            </script>""", shared=True)
        ui.on('js_error', lambda e: logger.error('Erreur JavaScript : %s', e.args))

    def _build_drawer(self) -> None:
        """Construit le volet de gauche avec les différentes impressions/extractions à générer"""
        groups = [
            self._menu_items_group1(),
            self._menu_items_group2(),
            self._menu_items_group3(),
        ]
        with ui.left_drawer().classes('bg-blue-100') as self.left_drawer:
            with ui.column().classes('w-full h-full no-wrap gap-0'):
                for i, items in enumerate(groups):
                    if i:
                        ui.separator()
                    with ui.list().classes('w-full py-1'):
                        for icon, label, handler in items:
                            self._add_menu_item(icon, label, handler)

    def _menu_items_group1(self) -> list[tuple]:
        """Entrées du groupe 1 du menu : (icône, libellé, action)."""
        per_year = [
            ('sym_o_signature', "Emargement", self._generate_attendance),
            ('sym_o_room_service', "Règlement repas", self._generate_meal),
            ('sym_o_receipt_long', "Factures", self._generate_invoices),
        ]
        return [
            (icon, f'{label} (année {year})', partial(handler, year))
            for icon, label, handler in per_year
            for year in (1, 2)
        ]

    def _menu_items_group2(self) -> list[tuple]:
        """Entrées du groupe 2 du menu: (icône, libellé, action)."""
        return [
            ('sym_o_mail', 'Etiquettes courriers', self._generate_mails),
            ('sym_o_files', 'Etiquettes dossiers', self._generate_files),
            ('sym_o_badge', 'Badges', self._generate_badges),
        ]

    def _menu_items_group3(self) -> list[tuple]:
        """Entrées du groupe 3 du menu : (icône, libellé, action)."""
        return [
            ('sym_o_table_view', 'Export excel', self._export_excel),
        ]

    def _add_menu_item(self, icon_name, label, fonction):
        """Ajoute un item de menu dans le panneau de gauche"""
        with ui.item(on_click=fonction):
            with ui.item_section().props('avatar'):
                ui.icon(icon_name)
            with ui.item_section():
                ui.item_label(label)

    def _build_tabs(self):
        """Construction des onglets"""
        with ui.header().classes(replace='row items-center') as header:
            ui.button(on_click=lambda: self.left_drawer.toggle(), icon='menu').props('flat color=white')
            etat = {'titre': 'Promotion'}
            with ui.tabs().props('inline-label') as self.tabs:
                with ui.tab(name='promo', label=''):
                    self._promotion_label = ui.label().style('font-size: 14px !important')
                with ui.tab('participants') as self._tab_participants:
                    self._participants_badge = ui.badge(color='grey', text_color='white').classes('ml-2')
                with ui.tab('animators', label='Animateurs').style('font-size: 18px !important'):
                    self._animators_badge = ui.badge(color='grey', text_color='white').classes('ml-2')
                with ui.tab('addressees', label='Destinataires').style('font-size: 18px !important'):
                    self._addressees_badge = ui.badge(color='grey', text_color='white').classes('ml-2')
                with ui.tab('senders', label='Envoyants').style('font-size: 18px !important') as self._tab_senders:
                    self._senders_badge = ui.badge(color='grey', text_color='white').classes('ml-2')
                ui.tab('info', label='Configuration', icon='settings').style('font-size: 18px !important')
                ui.tab('apropos', label='A PROPOS', icon='info').style('font-size: 18px !important')
            self._update_promotion_information()
            self._on_animators_changed(self.session_state.session_id)
            self._on_senders_changed(self.session_state.session_id)
            self._on_adressees_changed(self.session_state.session_id)

    def _subscribe_changes(self):
        """Inscriptions aux changements"""
        database_controller.subscribe_senders_changed(self._on_senders_changed)
        database_controller.subscribe_addressees_changed(self._on_adressees_changed)
        database_controller.subscribe_animators_changed(self._on_animators_changed)
        database_controller.subscribe_promotion_changed(self._update_promotion_information)
        database_controller.subscribe_participants_changed(self._update_participants_badge)

    def _unsubscribe_changes(self):
        database_controller.unsubscribe_senders_changed(self._on_senders_changed)
        database_controller.unsubscribe_addressees_changed(self._on_adressees_changed)
        database_controller.unsubscribe_animators_changed(self._on_animators_changed)

        # TODO : Implémenter cette méthode

    def _on_senders_changed(self, origin, op=None, payload=None):
        """Mise à jour des envoyants - par soi-même ou par une autre sessions"""
        self._senders_badge.text = str(len(database_controller.get_senders()))
        if origin == self.session_state.session_id:
            return
        self._senders_tab.apply_remote_change(op, payload)        

    def _on_adressees_changed(self, origin, op=None, payload=None):
        """Mise à jour du nombre de destinataires dans le badge de l'onglet destinataires"""
        self._addressees_badge.text = str(len(database_controller.get_addressees()))
        if origin == self.session_state.session_id:
            return
        self._addressees_tab.apply_remote_change(op, payload)        

    def _on_animators_changed(self, origin, op=None, payload=None):
        """Mise à jour du nombre d'animateurs dans le badge de l'onglet animateurs"""
        self._animators_badge.text = str(len(database_controller.get_animators()))
        if origin == self.session_state.session_id:
            return
        self._animators_tab.apply_remote_change(op, payload)        

    def _update_promotion_information(self):
        """Mise à jour du nombre d'animateurs dans le badge de l'onglet animateurs"""
        promotion = self.session_state.promotion
        if promotion:
            self._promotion_label.text = f"Promotion {promotion.year} - {promotion.year + 2}"
        else:
            self._promotion_label.text = f"Gestion des promotions"
        self._update_participants_badge()

    def _update_participants_badge(self):
        promotion = self.session_state.promotion
        n = len(promotion.participants) if promotion else 0
        self._participants_badge.text = str(n)

    def _show_participants(self, label: str):
        """Basculer vers l'onglet des participants (à partir de l'onglet des envoyants) en filtrant sur l'envoyant"""
        self.tabs.set_value(self._tab_participants)
        self._participants_tab.filter_by_sender(label)

    def _build_tab_pages(self):
        """Construit les pages des onglets"""
        with ui.tab_panels(self.tabs, value='promo').classes('w-full grow'):
            with ui.tab_panel('promo'):
                PromotionTab(self.session_state)
            with ui.tab_panel('participants').classes('flex flex-col min-h-0'):
                self._participants_tab = ParticipantsTab(self.session_state)
            with ui.tab_panel('animators').classes('flex flex-col min-h-0'):
                self._animators_tab = AnimatorsTab(self.session_state)                
            with ui.tab_panel('addressees').classes('flex flex-col min-h-0'):
                self._addressees_tab = AddresseesTab(self.session_state)
            with ui.tab_panel('senders').classes('flex flex-col min-h-0'):
                self._senders_tab = SendersTab(self.session_state, on_show_participants=self._show_participants)                
            with ui.tab_panel('info'):
                InformationTab(self.session_state)
            with ui.tab_panel('apropos'):
                AboutTab()                

    def _generate_attendance(self, year):
        """Génère les feuilles d'émargement"""
        promotion = self.session_state.promotion
        information = database_controller.load_information()
        try:
            pdf = AttendanceController(promotion.participants, "Feuille d'émargement",
                f"{information.name} {promotion.year}-{promotion.year + 2} - Année {promotion.year + year-1}-{promotion.year + year}",
                int(os.getenv("ATTENDANCE_FROM")), int(os.getenv("ATTENDANCE_TO"))).generate()
            ui.download(pdf, f"emargement_{promotion.year + year-1}_{promotion.year + year}.pdf")
        except ValueError as e:
            ui.notify(str(e), type='warning')

    def _generate_meal(self, year):
        """Génère les feuilles de paiement des repas"""
        try:
            promotion = self.session_state.promotion
            information = database_controller.load_information()
            pdf = MealController(promotion.participants, "Règlement des repas",
                f"{information.name} {promotion.year}-{promotion.year + 2} - Année {promotion.year + year-1}-{promotion.year + year}").generate()
            ui.download(pdf, f"repas_{promotion.year + year-1}_{promotion.year + year}.pdf")
        except ValueError as e:
            ui.notify(str(e), type='warning')

    async def _generate_invoices(self, year):
        """Génère les factures"""
        promotion = self.session_state.promotion
        controller = InvoiceController(
            promotion.participants, database_controller.get_senders(),
            database_controller.load_information(),
            fee=promotion.year_fee,
            logo_path=os.getenv('INVOICE_LOGO', 'assets/logo.png'),
            school_year=f'{promotion.year}-{promotion.year + 2}',
            year=promotion.year + year - 1
        )
        if controller.without_sender or controller.unknown_sender:
            await self._show_invoice_problems(controller)
            return                                   # rien n'est généré
        try:
            pdf = controller.generate()
        except ValueError as e:
            ui.notify(str(e), type='warning')
            return
        ui.download(pdf, 'factures.pdf')

    async def _show_invoice_problems(self, controller):
        """Affiche un problème lors de la génération des factures"""
        def name(p) -> str:
            return ' '.join(x.strip() for x in (p.firstname, p.name) if x and x.strip())

        with ui.dialog().props('persistent') as dialog, ui.card().classes('w-[480px]'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('error', color='negative', size='md')
                ui.label('Impossible de générer les factures').classes('text-lg font-bold')

            if controller.without_sender:
                ui.label(f"{len(controller.without_sender)} participant(s) sans envoyant :") \
                    .classes('font-bold')
                with ui.column().classes('w-full gap-0 max-h-40 overflow-auto'):
                    for p in controller.without_sender:
                        ui.label(f'• {name(p)}')

            if controller.unknown_sender:
                ui.label(f"{len(controller.unknown_sender)} participant(s) ont un envoyant qui "
                         "n'existe pas dans la liste :").classes('font-bold')
                with ui.column().classes('w-full gap-0 max-h-40 overflow-auto'):
                    for p in controller.unknown_sender:
                        ui.label(f'• {name(p)} : « {p.sender_label} »')

            ui.label("Corrigez la colonne « Envoyé par » dans l'onglet des participants, "
                     "puis relancez la génération.").classes('text-sm text-gray-600')
            with ui.row().classes('w-full justify-end'):
                ui.button('Fermer', on_click=dialog.close)

        dialog.open()
        await dialog
        dialog.delete()        
        
    def _generate_mails(self):
        """Génère les étiquettes de courriers"""
        try:        
            promotion = self.session_state.promotion
            persons = sorted(promotion.participants + database_controller.get_addressees(), key=lambda p: p.name)
            information = database_controller.load_information()
            pdf = MailLabelController(persons, information.mail_tag).generate()
            ui.download(pdf, f"courrier_{promotion.year}_{promotion.year + 2}.pdf")
        except ValueError as e:
            ui.notify(str(e), type='warning')

    async def _generate_files(self):
        """Génère les étiquettes des dossiers pour une intervention donnée"""
        intervention = await self._ask_intervention()
        if intervention is None:
            return
        promotion = self.session_state.promotion
        persons = promotion.participants + database_controller.get_animators()
        information = database_controller.load_information()
        try:
            pdf = FileLabelController(persons, intervention, information.file_tag, extra_identities=('INTERVENANT', 'ARCHIVE')).generate()
            ui.download(pdf, f"dossier.pdf")
        except ValueError as e:
            ui.notify(str(e), type='warning')

    async def _ask_intervention(self) -> dict | None:
        """Demande les informations de l'intervention"""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label("Détail de l'intervention").classes('text-lg font-bold')

            speaker = ui.input("Nom de l'intervenant",
                            validation={'Champ obligatoire': required}, value=self.last_speaker).classes('w-full')
            title = ui.input("Titre de l'intervention",
                            validation={'Champ obligatoire': required}, value=self.last_title).classes('w-full')

            # date : saisie au clavier (JJ/MM/AAAA) ou choix dans un calendrier
            with ui.input("Date de l'intervention",
                        validation={'Date invalide (JJ/MM/AAAA)': valid_date}, value=to_display(self.last_intervention_date)).classes('w-full') as date_input:
                with ui.dialog() as cal_dialog, ui.card():
                    with ui.date(mask='DD/MM/YYYY').bind_value(date_input):
                        with ui.row().classes('justify-end'):
                            ui.button('Fermer', on_click=cal_dialog.close).props('flat')
                with date_input.add_slot('append'):
                    ui.icon('edit_calendar').on('click', cal_dialog.open).classes('cursor-pointer')

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
        self.last_speaker = result['speaker']
        self.last_title = result['title']
        self.last_intervention_date = result['date']
        dialog.delete()   # évite d'accumuler des dialogues dans la page
        return result        

    def _generate_badges(self):
        """Génère les badges"""
        try:
            promotion = self.session_state.promotion
            tag = database_controller.load_information().badge_tag
            pdf = BadgeController(
                self.session_state.promotion.participants, tag,
                logo_path=os.getenv('BADGE_LOGO', 'assets/logo.png'),
                font_path=os.getenv('BADGE_FONT', 'assets/comicbd.ttf'),
            ).generate()
            ui.download(pdf, f"badges_{promotion.year}_{promotion.year + 2}.pdf")
        except ValueError as e:
            ui.notify(str(e), type='warning')

    def _export_excel(self):
        """Export les données au format excel"""
        promotion = self.session_state.promotion
        data = ExportExcelController(
            promotion.participants,
            database_controller.get_animators(),
            database_controller.get_addressees(),
            database_controller.get_senders(),
        ).generate()
        ui.download(data, f'export_{promotion.year}-{promotion.year + 2}.xlsx')            

