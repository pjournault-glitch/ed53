from sqlalchemy import delete, func, select
from controller.database import SessionLocal
from model.model import Addressee, Animator, Information, Participant, Promotion, Sender
from model.database_model import DbInformation, DbPersonne, DbPromotion

PERSON_FIELDS = {"sender": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail", "organisation"},
                 "addressee": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail"},
                 "animator": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail"},
                 "participant": {"title", "firstname", "name", "street", "zip", "city", "phone", "mail", "sender_label"}}

class DatabaseController:
    """Gestionnaire des données"""
    def __init__(self) -> None:

        self._senders_callbacks = []
        self._on_addressees_changed = []
        self._on_promotion_changed = []
        self._on_animators_changed = []
        self._on_participants_changed = []
        self._promotion = None
        self.promotion = self.load_promotion(self.get_latest_promotion())

    """Permet de s'abonner aux changements d'envoyants"""
    def subscribe_senders_changed(self, callback) -> None:
        self._senders_callbacks.append(callback)

    """Permet de se désabonner aux changements d'envoyants"""
    def unsubscribe_senders_changed(self, callback):
        self._senders_callbacks.remove(callback)        

    """Notifie les abonnés aux changements d'envoyant"""
    def notify_senders_changed(self, origin: str, op: str, payload):
        for callback in list(self._senders_callbacks):
            callback(origin, op, payload)   

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

    """Permet de s'abonner aux changements de participants"""
    def subscribe_participants_changed(self, callback) -> None:
        self._on_participants_changed.append(callback)

    """Notifie les abonnés aux changement de participants"""
    def _notify_participants_changed(self) -> None:
        for callback in self._on_participants_changed:
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
        self._notify_participants_changed()

    """Permet de s'abonner aux changements de promotion en cours"""
    def subscribe_promotion_changed(self, callback) -> None:
        self._on_promotion_changed.append(callback)

    """Notifie les abonnés aux changement de promotion en cours"""
    def _notify_promotion_changed(self) -> None:
        for callback in self._on_promotion_changed:
            callback()

    # Promotion ---------------------------------------------------------------------------------------------------------

    """Renvoi la liste des promotions existantes"""
    def existing_promotions(self) -> list[int]:
        with SessionLocal() as session:
            return [p.year for p in session.scalars(select(DbPromotion).order_by(DbPromotion.year.desc())).all()]

    """Enregistre une promotion"""
    def save_promotion(self, promotion: Promotion) -> DbPromotion:
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

    """Renvoi l'id de la dernière promotion"""
    def get_latest_promotion_id(self) -> int | None:        
        latest_year = self.get_latest_promotion()
        if not latest_year:
            return None
        with SessionLocal() as session:
            return session.scalar(select(DbPromotion.id).where(DbPromotion.year == latest_year))

    """Renvoi une promotion par son id"""
    def get_promotion_by_id(self, id) -> Promotion | None:
        with SessionLocal() as session:
            db_promotion = session.scalar(select(DbPromotion).where(DbPromotion.id == id))
            if not db_promotion:
                return None 
            return db_promotion.to_entity()

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

    # Participants ------------------------------------------------------------------------------------------------------------

    """Renvoi les participants de la promotion donnée"""
    def get_participants(self, promotion) -> list[Participant]:
        with SessionLocal() as session:
            db_participants = session.scalars(select(DbPersonne).where(DbPersonne.promotion_id == promotion.id, DbPersonne.type == "participant").order_by(DbPersonne.name, DbPersonne.firstname)).all()
            return [
                Participant(id=r.id, **{f: getattr(r, f) or "" for f in PERSON_FIELDS["participant"]})
                for r in db_participants
            ]  

    """Ajoute un participant à la promotion donnée"""
    def add_participant(self, promotion, data: dict) -> int:
        with SessionLocal() as session:
            p = DbPersonne(type="participant", promotion_id=promotion.id, **{k: v for k, v in data.items() if k in PERSON_FIELDS["participant"]})
            session.add(p)
            session.commit()
            self._promotion = self.load_promotion(self.promotion.year)
            self._notify_participants_changed()
            return p.id

    """Met à jour un participant"""
    def update_participant(self, data: dict) -> None:
        self._update_person("participant", data)
        self._promotion = self.load_promotion(self.promotion.year)
        self._notify_participants_changed()

    """Supprime des participants"""
    def delete_participants(self, ids: set[int]) -> None:
        self._delete_persons(ids)
        self._promotion = self.load_promotion(self.promotion.year)
        self._notify_participants_changed()        

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
        return id

    """Met à jour un envoyant"""
    def update_sender(self, data: dict) -> None:
        self._update_person("sender", data)

    """Supprime des envoyants"""
    def delete_senders(self, ids: set[int]) -> None:
        self._delete_persons(ids)

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
