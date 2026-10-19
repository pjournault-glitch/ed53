
import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)

from util.logging import install_asyncio_handler, log_user_action, setup_logging

setup_logging(getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO))

from fastapi import HTTPException
from nicegui import app, ui

from controller.database_controller import database_controller
from main_window import MainWindow
from model.session_state import SessionState
from tabs.promotion_tab import PromotionTab
from util.util import required_label


PASSWORD_EDIT = os.environ['APP_PASSWORD_EDIT']
PASSWORD_READ = os.environ['APP_PASSWORD_READ']
assert PASSWORD_EDIT != PASSWORD_READ, 'Les deux mots de passe doivent être différents'

logger = logging.getLogger('app')

ui.add_css('.q-tab__label { font-size: 14px; }', shared=True)
ui.add_css('body { font-size: 12px; }', shared=True)
ui.add_css('.nicegui-markdown :is(h1,h2,h3,h4,h5,h6) { scroll-margin-top: 70px; }', shared=True)
ui.add_css('''
.nicegui-markdown.aide-md {
    font-size: 15px; line-height: 1.7; max-width: 52rem; color: #1f2328;
}
.nicegui-markdown.aide-md :is(h1, h2, h3, h4) {
    font-weight: 600; line-height: 1.3; scroll-margin-top: 70px;
}
.nicegui-markdown.aide-md h1 {
    font-size: 2em; margin: 0 0 .8em; padding-bottom: .3em; border-bottom: 1px solid #d1d9e0;
}
.nicegui-markdown.aide-md h2 {
    font-size: 1.6em; margin: 1.8em 0 .8em; padding-bottom: .3em; border-bottom: 1px solid #d1d9e0;
}
.nicegui-markdown.aide-md h3 { font-size: 1.25em; margin: 1.5em 0 .6em; }
.nicegui-markdown.aide-md h4 { font-size: 1.05em; margin: 1.2em 0 .5em; }

.nicegui-markdown.aide-md p { margin: 0 0 1em; }
.nicegui-markdown.aide-md :is(ul, ol) { margin: 0 0 1em; padding-left: 2em; }
.nicegui-markdown.aide-md li { margin: .5em 0; }
.nicegui-markdown.aide-md li > p { margin: .4em 0; }

.nicegui-markdown.aide-md code {
    font-size: 90%; padding: .15em .4em; border-radius: 4px; background: #eff1f3;
}
.nicegui-markdown.aide-md table { border-collapse: collapse; margin: 0 0 1em; }
.nicegui-markdown.aide-md :is(th, td) { border: 1px solid #d1d9e0; padding: 6px 12px; }
.nicegui-markdown.aide-md th { font-weight: 600; background: #f6f8fa; }
.nicegui-markdown.aide-md blockquote {
    margin: 0 0 1em; padding: 0 1em; color: #59636e; border-left: 4px solid #d1d9e0;
}
''', shared=True)
ui.add_css('''
.nb-chip {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 30px; height: 22px; padding: 0 10px; border-radius: 11px;
    background: #e3f2fd; color: #1565c0; font-weight: 600; font-size: 12px;
    cursor: pointer; transition: background .15s, color .15s;
}
.nb-chip:hover { background: #1976d2; color: #fff; }
.nb-chip-zero { color: #9e9e9e; }
.ag-center-header .ag-header-cell-label { justify-content: center; }
''', shared=True)
ui.add_head_html("""
                    <script>
                    window.addEventListener('error', e => emitEvent('js_error',
                        {message: e.message, source: e.filename, line: e.lineno}));
                    window.addEventListener('unhandledrejection', e => emitEvent('js_error',
                        {message: String(e.reason), source: 'promise', line: 0}));
                    </script>""", shared=True)

def _role_for(password: str) -> str | None:
    pw = password.encode()
    if secrets.compare_digest(pw, PASSWORD_EDIT.encode()):
        return 'edit'
    if secrets.compare_digest(pw, PASSWORD_READ.encode()):
        return 'read'
    return None

@app.on_startup
async def _on_startup():
    install_asyncio_handler(logger)
    logger.info(f"Application démarrée PID={os.getpid()}")

@app.on_exception
def _on_exception(exception: Exception):
    """Appelé par NiceGUI pour toute erreur dans un handler (clic, événement de grille, timer…)."""
    logger.error('Erreur dans l\'interface', exc_info=exception)
    try:
        ui.notify("Une erreur est survenue. Elle a été enregistrée dans le journal.", type='negative')
    except Exception:
        pass

@ui.page('/login')
def login():
    def try_login():
        name = (nom.value or '').strip()
        if not name:
            ui.notify('Veuillez saisir votre nom', color='negative')
            return
        role = _role_for(password.value)
        if role is None:
            ui.notify('Mot de passe incorrect', color='negative')
            return        
        app.storage.user['authenticated'] = True
        app.storage.user['role'] = role
        app.storage.user['name'] = name
        log_user_action(name, 'connexion', 'application', f'rôle={role}')
        ui.navigate.to('/')

    with ui.card().classes('absolute-center w-96 max-w-[100vw]'):
        with ui.column().classes('w-full items-center gap-2 mb-4'):
            ui.image(str(Path(__file__).resolve().parent / 'assets' / 'logo.png')).classes('w-24')
            ui.label('École du diocèse de Laval').classes('text-h6 text-center')
            ui.label(
                'Merci de saisir votre nom et le mot de passe qui vous a été fourni '
                'pour vous connecter à l’application.'
            ).classes('text-center text-grey-7')
        nom = required_label(
            ui.input('Votre nom', validation={'Ce champ est obligatoire': lambda value: bool(value and value.strip())}),
            'Votre nom',
        ).classes('w-full').on('keydown.enter', try_login)
        password = ui.input('Mot de passe', password=True, password_toggle_button=True).on('keydown.enter', try_login)
        password = required_label(password, 'Mot de passe').classes('w-full')
        password.props('required')
        ui.button('Connexion', on_click=try_login)

@ui.page('/')
def index():
    if not app.storage.user.get('authenticated'):
        return ui.navigate.to('/login')
    latest = database_controller.get_latest_promotion_id()
    ui.navigate.to(f'/promotion/{latest}' if latest else '/promotion/new')    

@ui.page('/promotion/new')
def new_promotion_page():
    if not app.storage.user.get('authenticated'):
        return ui.navigate.to('/login')
    if app.storage.user.get('role') != 'edit':
        with ui.card().classes('absolute-center'):
            ui.label('Aucune promotion n’est encore créée.')
            ui.label('Connectez-vous avec le mot de passe de modification pour créer la première.')
            ui.button('Retour à la connexion', on_click=lambda: ui.navigate.to('/login'))
        return
    PromotionTab(SessionState(
        None,
        ui.context.client.id,
        app.storage.user.get('name') or '',
        can_edit=True,
    ))

@ui.page('/promotion/{promotion_id}')
def promotion_page(promotion_id: int):
    if not app.storage.user.get('authenticated'):
        return ui.navigate.to('/login')
    if database_controller.get_promotion_by_id(promotion_id): 
        MainWindow(SessionState(promotion_id, ui.context.client.id, app.storage.user.get('name'), can_edit=app.storage.user.get('role') == 'edit'))
    else:
        raise HTTPException(status_code=404, detail='Promotion introuvable')

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Ecole du diocèse',
        language='fr',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8080)),
        reload=False,
        show=False,                                   # pas d'ouverture de navigateur
        storage_secret=os.environ['STORAGE_SECRET'],  # nécessaire pour la connexion (point 3)
    )    