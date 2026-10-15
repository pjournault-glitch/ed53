
import logging
import os
from pathlib import Path
import sys

from nicegui import app, ui
from dotenv import load_dotenv

from controller.database_controller import database_controller
from main_window import MainWindow
from model.session_state import SessionState
from util.logging import install_asyncio_handler, setup_logging


BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
LOG_FILE = setup_logging(BASE_DIR / 'logs', getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO))
PASSWORD = os.environ['APP_PASSWORD']

load_dotenv(override=False)
logger = logging.getLogger('app')
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


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
        pass            # pas de contexte d'interface disponible : l'erreur est de toute façon dans le journal

@ui.page('/login')
def login():
    def try_login():
        if password.value == PASSWORD:
            app.storage.user['authenticated'] = True
            ui.navigate.to('/')
        else:
            ui.notify('Mot de passe incorrect', color='negative')

    with ui.card().classes('absolute-center'):
        password = ui.input('Mot de passe', password=True, password_toggle_button=True) \
            .on('keydown.enter', try_login)
        ui.button('Connexion', on_click=try_login)

@ui.page('/')
def index():
    if not app.storage.user.get('authenticated'):
        return ui.navigate.to('/login')
    latest = database_controller.get_latest_promotion_id()
    ui.navigate.to(f'/promotion/{latest}' if latest else '/promotion/new')    

@ui.page('/promotion/{promotion_id}')
def promotion_page(promotion_id: int):
    if not app.storage.user.get('authenticated'):
        return ui.navigate.to('/login')
    MainWindow(SessionState(promotion_id))  

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