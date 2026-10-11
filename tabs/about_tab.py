import os

from dotenv import load_dotenv
from nicegui import ui

APP_NAME = os.getenv('APP_NAME', 'Ecole du diocèse')
APP_VERSION = os.getenv('APP_VERSION', '?')
APP_AUTHOR = os.getenv('APP_AUTHOR', '')
APP_EMAIL = os.getenv('APP_EMAIL', '')
APP_YEAR = os.getenv('APP_YEAR', '')


class AboutTab:
    def __init__(self):
        load_dotenv(override=True)
        with ui.column().classes('w-full items-center gap-2 mt-16'):
            ui.label(APP_NAME).classes('text-4xl font-bold')
            ui.label(f'Version {APP_VERSION}').classes('text-lg text-gray-600')
            ui.separator().classes('w-64 my-4')
            ui.label(f'© {APP_YEAR} {APP_AUTHOR} ({APP_EMAIL})').classes('text-gray-500')
            ui.label('Tous droits réservés').classes('text-sm text-gray-400')