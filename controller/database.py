import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger('app')

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

logger.info("Initialisation du moteur de base de données")
logger.debug(DATABASE_URL)
engine = create_engine(DATABASE_URL, echo=False)
if engine:
    logger.info("Connecté à la base de données")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
else:    
    logger.info("Connexion impossible")
