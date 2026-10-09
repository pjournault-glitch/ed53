from dataclasses import asdict
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from model.model import Addressee, Animator, Information, Promotion, Sender

INFORMATION_FILE = "information.json"
SENDERS_FILE = "senders.json"
ANIMATORS_FILE = "animators.json"
ADDRESSEE_FILE = "addressees.json"

class DatabaseController:
    """Gestionnaire des données"""
    def __init__(self) -> None:
        load_dotenv()
        self.db_path = Path(os.getenv("DATABASE", "db"))
        self._on_promotion_changed = []
        self._promotion = None
        self.promotion = self.load_promotion(self.get_latest_promotion())
        self._on_senders_changed = []
        self._senders = []
        self.senders = self.load_senders()
        self._on_animators_changed = []
        self._animators = []
        self.animators = self.load_animators()
        self._on_addressees_changed = []
        self._addressees = []
        self.addressees = self.load_addressees()

    """Renvoi la promotion en cours d'utilisation"""
    @property
    def promotion(self) -> Promotion:
        return self._promotion

    """Choisi la promotion en cours et notifie les abonnés à ce changement"""
    @promotion.setter
    def promotion(self, value:Promotion) -> None:
        self._promotion = value
        for callback in self._on_promotion_changed:
            callback()

    """Permet de s'abonner aux changements de promotion en cours"""
    def subscribe_promotion_changed(self, callback) -> None:
        self._on_promotion_changed.append(callback)

    """Renvoi la liste des envoyants en cours d'utilisation"""
    @property
    def senders(self) -> list[Sender]:
        return self._senders

    """Définit la liste des envoyants en cours et notifie les abonnés à ce changement"""
    @senders.setter
    def senders(self, value: list[Sender]) -> None:
        self._senders = value
        for callback in self._on_senders_changed:
            callback()

    """Permet de s'abonner aux changements dans les envoyants en cours"""
    def subscribe_senders_changed(self, callback) -> None:
        self._on_senders_changed.append(callback)        

    """Renvoi la liste des animateurs en cours d'utilisation"""
    @property
    def animators(self) -> list[Animator]:
        return self._animators

    """Définit la liste des animateurs en cours et notifie les abonnés à ce changement"""
    @animators.setter
    def animators(self, value: list[Animator]) -> None:
        self._animators = value
        for callback in self._on_animators_changed:
            callback()

    """Permet de s'abonner aux changements dans les animateurs en cours"""
    def subscribe_animators_changed(self, callback) -> None:
        self._on_animators_changed.append(callback)        

    """Renvoi la liste des destinataires en cours d'utilisation"""
    @property
    def addressees(self) -> list[Addressee]:
        return self._addressees

    """Définit la liste des destinataires en cours et notifie les abonnés à ce changement"""
    @addressees.setter
    def addressees(self, value: list[Addressee]) -> None:
        self._addressees = value
        for callback in self._on_addressees_changed:
            callback()

    """Permet de s'abonner aux changements dans les destinataires en cours"""
    def subscribe_addressees_changed(self, callback) -> None:
        self._on_addressees_changed.append(callback)        

    """Renvoi l'année de la promotion en cours"""
    @property
    def promotion_year(self) -> int:
        return self.promotion.year if self.promotion else None

    """Renvoi le nom de fichier de la dernière promotion"""
    def get_latest_promotion_file(self) -> str:
        db_file_names = [p.name for p in self.db_path.iterdir() if p.is_file() and p.name.startswith("promotion_")]
        return max(db_file_names, key=str.casefold, default=None)

    """Renvoi l'année de la dernière promotion, à partir du nom du fichier"""
    def get_latest_promotion(self) -> int:
        return int(Path(self.get_latest_promotion_file()).stem[10:])

    """Charge une promotion, définie par son année"""
    def load_promotion(self, year: int) -> Promotion:
        name = Path(self.db_path) / f"promotion_{year}.json"
        with open(name, encoding='utf-8') as f:
            return Promotion.from_dict(json.load(f))

    """Enregistre une promotion"""
    def save_promotion(self, promotion:Promotion) -> None:        
        name = Path(self.db_path) / f"promotion_{promotion.year}.json"
        tmp = f"{name}.tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(asdict(promotion), f, ensure_ascii=False, indent=4)
        os.replace(tmp, name)        

    """Renvoi la liste des promotions existantes"""
    def existing_promotions(self) -> list[int]:
        return [int(Path(p.name).stem[10:]) for p in self.db_path.iterdir() if p.is_file() and p.name.startswith("promotion_")]

    """Vérifie si une promotion existe par son année (ou année -1, puisqu'une promotion dure 2 ans)"""
    def promotion_exists(self, year:int) -> bool:
        return year in self.existing_promotions() or (year - 1) in self.existing_promotions()

    """Charge les informations générales"""
    def load_information(self) -> Information:
        name = Path(self.db_path) / INFORMATION_FILE
        with open(name, encoding='utf-8') as f:
            return Information.from_dict(json.load(f))

    """Enregistre les informations générales"""
    def save_information(self, information:Information) -> None:        
        name = Path(self.db_path) / INFORMATION_FILE
        tmp = f"{name}.tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(asdict(information), f, ensure_ascii=False, indent=4)
        os.replace(tmp, name) 

    """Charge les envoyants"""
    def load_senders(self) -> dict[str, Sender]:
        path = Path(self.db_path) / SENDERS_FILE
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [Sender(**s) for s in data]

    """Enregistre les envoyants"""
    def save_senders(self) -> None:
        path = Path(self.db_path) / SENDERS_FILE
        data = [asdict(s) for s in self.senders]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")         

    """Renvoie tous les envoyants"""
    def get_all_senders(self) -> list[Sender]:
        return sorted(self.senders, key=lambda s: s.label.lower())

    """Renvoie un envoyant par son id"""
    def get_sender(self, sender_id: str | None) -> Sender | None:
        return next((o for o in self.senders if o.id == sender_id), None)

    """Charge les animateurs"""
    def load_animators(self) -> dict[str, Animator]:
        path = Path(self.db_path) / ANIMATORS_FILE
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [Animator(**s) for s in data]

    """Enregistre les animateurs"""
    def save_animators(self) -> None:
        path = Path(self.db_path) / ANIMATORS_FILE
        data = [asdict(s) for s in self.animators]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")         
    
    """Charge les destinataires"""
    def load_addressees(self) -> dict[str, Addressee]:
        path = Path(self.db_path) / ADDRESSEE_FILE
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [Addressee(**s) for s in data]

    """Enregistre les destinataires"""
    def save_animators(self) -> None:
        path = Path(self.db_path) / ADDRESSEE_FILE
        data = [asdict(s) for s in self.addressees]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")         

database_controller = DatabaseController()
