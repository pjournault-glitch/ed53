import asyncio
from contextlib import contextmanager
import logging
import sys
import threading
from collections.abc import Iterator

_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'


def setup_logging(level: int = logging.INFO) -> None:
    """Configure le journal sur la console. À appeler une seule fois au démarrage."""
    root = logging.getLogger()
    if any(getattr(handler, '_ed_console_handler', False) for handler in root.handlers):
        return

    formatter = logging.Formatter(_FORMAT)
    handlers: list[logging.Handler] = []
    if sys.stderr:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler._ed_console_handler = True
        handlers.append(console_handler)
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

    if sys.stderr:
        import faulthandler
        faulthandler.enable(file=sys.stderr)

    logger.info('Journal démarré (Python %s)', sys.version.split()[0])


def log_user_action(user: str, action: str, entity: str, details: str = '') -> None:
    """Écrit une trace d'audit sans inclure les valeurs des données modifiées."""
    safe_user = user.replace('\r', ' ').replace('\n', ' ').strip()
    logging.getLogger('app').info(
        'AUDIT utilisateur=%s action=%s entité=%s%s',
        safe_user,
        action,
        entity,
        f' {details}' if details else '',
    )


@contextmanager
def log_generation(user: str, file_format: str, filename: str) -> Iterator[None]:
    """Journalise le début et la fin d'une génération de document."""
    logger = logging.getLogger('app')
    user = user.replace('\r', ' ').replace('\n', ' ').strip()
    details = 'utilisateur=%s format=%s fichier=%s'
    logger.info('Génération début ' + details, user, file_format, filename)
    try:
        yield
    except Exception:
        logger.info('Génération fin résultat=échec ' + details, user, file_format, filename)
        raise
    else:
        logger.info('Génération fin résultat=succès ' + details, user, file_format, filename)


def install_asyncio_handler(logger: logging.Logger) -> None:
    """Capture les exceptions de tâches asynchrones jamais attendues (à appeler au démarrage du serveur)."""
    def handler(loop, context):
        logger.error('Erreur asynchrone : %s', context.get('message'), exc_info=context.get('exception'))
    asyncio.get_running_loop().set_exception_handler(handler)