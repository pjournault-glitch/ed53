from sqlalchemy import Column, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.mutable import MutableDict

from model.model import Information, Participant, Promotion, Tag


class Base(DeclarativeBase):
    pass


class DbPersonne(Base):
    __tablename__ = "personnes"

    id = Column(Integer, primary_key=True)
    type = Column(String(100), nullable=False)
    title = Column(String(10), nullable=True)
    firstname = Column(String(100), nullable=True)
    name = Column(String(100), nullable=True)
    street = Column(String(100), nullable=True)
    zip = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    mail = Column(String(100), nullable=True)
    organisation = Column(String(100), nullable=True)
    sender_label = Column(String(100), nullable=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=True)

    promotion = relationship("DbPromotion", back_populates="personnes")

    def to_participant(self):
        return Participant(title=self.title, firstname=self.firstname, name=self.name, street=self.street, zip=self.zip, city=self.city, phone=self.phone, mail=self.mail, sender_label=self.sender_label)


class DbPromotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    year_fee = Column(Float, nullable=False)

    personnes = relationship("DbPersonne", back_populates="promotion")

    def to_entity(self) -> Promotion:
        return Promotion(id=self.id, year=self.year, year_fee=self.year_fee, participants=[p.to_participant() for p in self.personnes])


class DbInformation(Base):
    __tablename__ = "information"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    addressee = Column(String(100), nullable=False)
    street = Column(String(100), nullable=False)
    bp = Column(String(100), nullable=True)
    zip = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    mail = Column(String(100), nullable=True)
    bic = Column(String(20), nullable=False)
    iban = Column(String(50), nullable=False)
    mail_tag = Column(MutableDict.as_mutable(JSON), nullable=True)
    file_tag = Column(MutableDict.as_mutable(JSON), nullable=True)
    badge_tag = Column(MutableDict.as_mutable(JSON), nullable=True)

    def from_entity(self, entity: Information) -> None:
        self.name = entity.name
        self.addressee = entity.addressee
        self.street = entity.street
        self.bp = entity.bp
        self.zip = entity.zip
        self.city = entity.city
        self.phone = entity.phone
        self.mail = entity.mail
        self.bic = entity.bic
        self.iban = entity.iban
        self.mail_tag = entity.mail_tag.to_dict() if entity.mail_tag else None
        self.file_tag = entity.file_tag.to_dict() if entity.file_tag else None
        self.badge_tag = entity.badge_tag.to_dict() if entity.badge_tag else None

    def to_entity(self) -> Information:
        return Information(name=self.name,
                           addressee=self.addressee,
                           street=self.street,
                           bp=self.bp,
                           zip=self.zip,
                           city=self.city,
                           phone=self.phone,
                           mail=self.mail,
                           bic=self.bic,
                           iban=self.iban,
                           mail_tag=Tag.from_dict(self.mail_tag),
                           file_tag=Tag.from_dict(self.file_tag),
                           badge_tag=Tag.from_dict(self.badge_tag))