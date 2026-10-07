from dataclasses import asdict
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from model.model import Information, Promotion


class DatabaseController:
    def __init__(self):
        load_dotenv()
        self.db_path = Path(os.getenv("DATABASE", "db"))

    def get_latest_promotion_file(self):
        db_file_names = [p.name for p in self.db_path.iterdir() if p.is_file()]
        return max(db_file_names, key=str.casefold, default=None)

    def get_latest_promotion(self):
        return Path(self.get_latest_promotion_file()).stem

    def load_promotion(self, file_name) -> Promotion:
        name = Path(self.db_path) / file_name
        with open(name, encoding='utf-8') as f:
            promotion = Promotion.from_dict(json.load(f))
            if not promotion.information:
                promotion.information = Information(name=os.getenv('NAME', ''), 
                                                    addressee=os.getenv('ADDRESSEE', ''),
                                                    street=os.getenv('STREET', ''),
                                                    bp=os.getenv('BP', ''),
                                                    zip=os.getenv('ZIP', ''),
                                                    city=os.getenv('CITY', ''),
                                                    phone=os.getenv('PHONE', ''),
                                                    mail=os.getenv('MAIL', ''),
                                                    bic=os.getenv('BIC', ''),
                                                    iban=os.getenv('IBAN', ''))
        return promotion 

    def save_promotion(self, promotion:Promotion):
        name = Path(self.db_path) / f"{promotion.year}.json"
        with open(name, 'w', encoding='utf-8') as f:
            json.dump(asdict(promotion), f, ensure_ascii=False, indent=4)        

database_controller = DatabaseController()
