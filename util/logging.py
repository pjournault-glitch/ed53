import asyncio
import faulthandler
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
_crash_file = None    # doit rester ouvert tant que le programme tourne


def setup_logging(log_dir: Path, level: int = logging.INFO) -> Path:
    """Configure le journal. À appeler une seule fois, au tout début du programme."""
    global _crash_file
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'application.log'

    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return log_file                                   # déjà configuré

    formatter = logging.Formatter(_FORMAT)
    handlers: list[logging.Handler] = [
        RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    ]
    if sys.stderr:                                         # absent quand lancé sans console (pythonw, .exe sans console)
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setFormatter(formatter)

    root.setLevel(level)
    for handler in handlers:
        root.addHandler(handler)
    # uvicorn et nicegui ne remontent pas au logger racine : on les branche directement
    for name in ('uvicorn', 'uvicorn.error', 'nicegui'):
        lg = logging.getLogger(name)
        lg.setLevel(level)
        for handler in handlers:
            lg.addHandler(handler)
    # bibliothèques bavardes : on ne garde que leurs avertissements et erreurs
    for name in ('watchfiles', 'httpx', 'httpcore', 'multipart', 'PIL', 'asyncio'):
        logging.getLogger(name).setLevel(logging.WARNING)
        
    logger = logging.getLogger('app')

    def excepthook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        logger.critical('Exception non interceptée', exc_info=(exc_type, exc, tb))

    sys.excepthook = excepthook
    threading.excepthook = lambda a: logger.critical(
        'Exception dans un thread', exc_info=(a.exc_type, a.exc_value, a.exc_traceback))

    # plantages brutaux de l'interpréteur (très rares) : trace écrite dans un fichier séparé
    _crash_file = open(log_dir / 'crash.log', 'a', encoding='utf-8')
    faulthandler.enable(file=_crash_file)

    logger.info('Journal démarré (Python %s)', sys.version.split()[0])
    return log_file


def install_asyncio_handler(logger: logging.Logger) -> None:
    """Capture les exceptions de tâches asynchrones jamais attendues (à appeler au démarrage du serveur)."""
    def handler(loop, context):
        logger.error('Erreur asynchrone : %s', context.get('message'), exc_info=context.get('exception'))
    asyncio.get_running_loop().set_exception_handler(handler)