import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger('app')

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("La variable d'environnement DATABASE_URL n'est pas définie")

database_url = make_url(DATABASE_URL)
if database_url.drivername in {'postgres', 'postgresql', 'postgresql+psycopg'}:
    database_url = database_url.set(drivername='postgresql+psycopg2')

logger.info("Initialisation du moteur de base de données")
engine = create_engine(database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
