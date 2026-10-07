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
        self.promotion = self.load_promotion(self.get_latest_promotion())

    @property
    def promotion_year(self):
        return self.promotion.year if self.promotion else None

    def get_latest_promotion_file(self):
        db_file_names = [p.name for p in self.db_path.iterdir() if p.is_file()]
        return max(db_file_names, key=str.casefold, default=None)

    def get_latest_promotion(self):
        return int(Path(self.get_latest_promotion_file()).stem)

    def load_promotion(self, year) -> Promotion:
        name = Path(self.db_path) / f"{year}.json"
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

    def existing_promotions(self):
        return [int(Path(p.name).stem) for p in self.db_path.iterdir() if p.is_file()]

    def promotion_exists(self, year):
        return year in self.existing_promotions() or (year - 1) in self.existing_promotions()

database_controller = DatabaseController()
