from asyncio.log import logger
from datetime import date
import logging
from dataclasses import asdict
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import delete, func, select
from controller.database import SessionLocal
from model.model import Addressee, Animator, Information, Promotion, Sender
from model.database_model import DbInformation, DbPersonne, DbPromotion

PERSON_FIELDS = {"sender": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail", "organisation"},
                 "addressee": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail"},
                 "animator": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail"}}

class DatabaseController:
    """Gestionnaire des données"""
    def __init__(self) -> None:
        load_dotenv()
        self.db_path = Path(os.getenv("DATABASE", "db"))
        self._on_senders_changed = []
        self._on_addressees_changed = []
        self._on_promotion_changed = []
        self._on_animators_changed = []
        self._promotion = None
        self.promotion = self.load_promotion(self.get_latest_promotion())

    """Permet de s'abonner aux changements d'envoyants"""
    def subscribe_senders_changed(self, callback) -> None:
        self._on_senders_changed.append(callback)

    """Notifie les abonnés aux changement d'envoyant"""
    def _notify_senders_changed(self) -> None:
        for callback in self._on_senders_changed:
            callback()

    """Permet de s'abonner aux changements dans les destinataires en cours"""
    def subscribe_addressees_changed(self, callback) -> None:
        self._on_addressees_changed.append(callback)        

    """Notifie les abonnés aux changement de destinataires"""
    def _notify_addressees_changed(self) -> None:
        for callback in self._on_addressees_changed:
            callback()

    """Permet de s'abonner aux changements dans les animateurs en cours"""
    def subscribe_animators_changed(self, callback) -> None:
        self._on_animators_changed.append(callback)        

    """Notifie les abonnés aux changement des animateurs"""
    def _notify_animators_changed(self) -> None:
        for callback in self._on_animators_changed:
            callback()

    """Renvoi la promotion en cours d'utilisation"""
    @property
    def promotion(self) -> Promotion:
        return self._promotion

    """Choisi la promotion en cours et notifie les abonnés à ce changement"""
    @promotion.setter
    def promotion(self, value:Promotion) -> None:
        self._promotion = value
        self._notify_promotion_changed()

    """Permet de s'abonner aux changements de promotion en cours"""
    def subscribe_promotion_changed(self, callback) -> None:
        self._on_promotion_changed.append(callback)

    """Notifie les abonnés aux changement de promotion en cours"""
    def _notify_promotion_changed(self) -> None:
        for callback in self._on_promotion_changed:
            callback()

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Écrit dans un fichier temporaire puis remplace : jamais de fichier à moitié écrit."""
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)

    def _write_json(self, path: Path, data, indent: int = 2) -> None:
        """Enregistre les données au format JSON, puis archive une copie datée."""
        content = json.dumps(data, ensure_ascii=False, indent=indent)
        self._atomic_write(path, content)
        self._archive(path, content)

    def _archive(self, path: Path, content: str) -> None:
        """Copie le contenu dans <db>/archive/<nom>_<AAAAMMJJ>.json (ex. animators_20261011.json)."""
        try:
            archive_dir = self.db_path / os.getenv("ARCHIVE")
            archive_dir.mkdir(parents=True, exist_ok=True)
            name = f"{path.stem}_{date.today():%Y%m%d}{path.suffix}"
            self._atomic_write(archive_dir / name, content)
        except OSError:
            # un échec d'archivage ne doit jamais empêcher l'enregistrement principal
            logger.exception("Archivage impossible pour %s", path.name)

    # Promotion ---------------------------------------------------------------------------------------------------------

    """Renvoi les participants de la promotion en cours"""
    def promotion_participants(self) -> list:
        with SessionLocal() as session:
            return session.scalars(
                select(DbPersonne)
                .where(DbPersonne.promotion_id == self.promotion_id,
                    DbPersonne.type == "participant")
                .order_by(DbPersonne.name, DbPersonne.firstname)
            ).all()

    """Renvoi la liste des promotions existantes"""
    def existing_promotions(self) -> list[int]:
        with SessionLocal() as session:
            return [p.year for p in session.scalars(select(DbPromotion).order_by(DbPromotion.year.desc())).all()]

    """Enregistre une promotion"""
    def save_promotion(self, promotion: Promotion) -> None:
        with SessionLocal() as session:
            db_promo = session.scalars(
                select(DbPromotion).where(DbPromotion.year == promotion.year)
            ).first()

            if db_promo is None:
                db_promo = DbPromotion(year=promotion.year, year_fee=promotion.year_fee)
                session.add(db_promo)
            else:
                db_promo.year_fee = promotion.year_fee

            session.commit()
            return db_promo.to_entity()      

    """Renvoi l'année de la dernière promotion"""
    def get_latest_promotion(self) -> int:
        with SessionLocal() as session:
            return session.scalar(select(func.max(DbPromotion.year)))

    """Charge une promotion, définie par son année"""
    def load_promotion(self, year: int) -> Promotion:
        with SessionLocal() as session:
            db_promotion = session.scalars(select(DbPromotion).where(DbPromotion.year == year)).first()
            return db_promotion.to_entity() if db_promotion else None

    """Vérifie si une promotion existe par son année (ou année -1, puisqu'une promotion dure 2 ans)"""
    def promotion_exists(self, year:int) -> bool:
        with SessionLocal() as session:
            return session.scalar(
                select(DbPromotion.id)
                .where(DbPromotion.year.in_([year, year - 1]))
                .limit(1)
            ) is not None

    # Personnes ------------------------------------------------------------------------------------------------------------

    """Charge des personnes"""
    def _get_persons(self, type) -> list:
        with SessionLocal() as session:
            return session.scalars(select(DbPersonne).where(DbPersonne.type == type).order_by(DbPersonne.id)).all()

    """Ajoute une personne"""
    def _add_person(self, type, data: dict) -> int:
        with SessionLocal() as session:
            p = DbPersonne(type=type, **{k: v for k, v in data.items() if k in PERSON_FIELDS[type]})
            session.add(p)
            session.commit()
            return p.id

    """Met à jour une personne"""
    def _update_person(self, type, data: dict) -> None:
        with SessionLocal() as session:
            p = session.get(DbPersonne, data["id"])
            if p:
                for k, v in data.items():
                    if k in PERSON_FIELDS[type]:
                        setattr(p, k, v)
                session.commit()

    """Supprime des personnes"""
    def _delete_persons(self, ids: set[int]) -> None:
        with SessionLocal() as session:
            session.execute(delete(DbPersonne).where(DbPersonne.id.in_(ids)))
            session.commit()
            self._notify_senders_changed()

    # Envoyants ------------------------------------------------------------------------------------------------------------

    """Charge les envoyants"""
    def get_senders(self) -> list[Sender]:
        return [
            Sender(id=r.id, **{f: getattr(r, f) or "" for f in PERSON_FIELDS["sender"]})
            for r in self._get_persons("sender")
        ]            

    """Ajoute un envoyant"""
    def add_sender(self, data: dict) -> int:
        id = self._add_person("sender", data)
        self._notify_senders_changed()
        return id

    """Met à jour un envoyant"""
    def update_sender(self, data: dict) -> None:
        self._update_person("sender", data)
        self._notify_senders_changed()

    """Supprime des envoyants"""
    def delete_senders(self, ids: set[int]) -> None:
        self._delete_persons(ids)
        self._notify_senders_changed()

    # Destinataires ------------------------------------------------------------------------------------------------------------

    """Charge les destinataires"""
    def get_addressees(self) -> list[Addressee]:
        return [
            Addressee(id=r.id, **{f: getattr(r, f) or "" for f in PERSON_FIELDS["addressee"]})
            for r in self._get_persons("addressee")
        ]            

    """Ajoute un destinataire"""
    def add_addressee(self, data: dict) -> int:
        id = self._add_person("addressee", data)
        self._notify_addressees_changed()
        return id

    """Met à jour un destinataire"""
    def update_addressee(self, data: dict) -> None:
        self._update_person("addressee", data)
        self._notify_addressees_changed()

    """Supprime des destinataires"""
    def delete_addressees(self, ids: set[int]) -> None:
        self._delete_persons(ids)
        self._notify_addressees_changed()

    # Animateurs ------------------------------------------------------------------------------------------------------------

    """Charge les animateurs"""
    def get_animators(self) -> list[Animator]:
        return [
            Animator(id=r.id, **{f: getattr(r, f) or "" for f in PERSON_FIELDS["animator"]})
            for r in self._get_persons("animator")
        ]            

    """Ajoute un animateur"""
    def add_animator(self, data: dict) -> int:
        id = self._add_person("animator", data)
        self._notify_animators_changed()
        return id

    """Met à jour un animateur"""
    def update_animator(self, data: dict) -> None:
        self._update_person("animator", data)
        self._notify_animators_changed()

    """Supprime des animateurs"""
    def delete_animators(self, ids: set[int]) -> None:
        self._delete_persons(ids)
        self._notify_animators_changed()

    # Informations --------------------------------------------------------------------------------------------------

    """Charge les informations générales"""
    def load_information(self) -> Information:
        with SessionLocal() as session:
            db_information = session.query(DbInformation).first()
            return db_information.to_entity()

    """Enregistre les informations générales"""
    def save_information(self, information: Information) -> None:
        with SessionLocal() as session:
            db_information = session.query(DbInformation).first()
            if db_information:
                db_information.from_entity(information)                
            else:
                db_information = DbInformation()
                db_information.from_entity(information)
                session.add(db_information)
            session.commit()

database_controller = DatabaseController()
