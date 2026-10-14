from controller.database import engine 
from model.database_model import Base

Base.metadata.create_all(bind=engine)
print("Tables créées")
