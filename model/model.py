from dataclasses import asdict, dataclass
import json

@dataclass
class Tag:
    margin_top: float
    margin_bottom: float 
    margin_left: float
    margin_right: float
    nb_horizontal: int 
    nb_vertical: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> 'Tag | None':
        return cls(**data) if data else None

@dataclass
class Information:
    name: str
    addressee: str
    street: str
    bp: str
    zip: str
    city: str
    phone: str
    mail: str
    bic: str
    iban: str
    mail_tag: Tag | None = None
    file_tag: Tag | None = None
    badge_tag: Tag | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Information':
        return cls(
            name=data['name'],
            addressee=data['addressee'],
            street=data['street'],
            bp=data['bp'],
            zip=data['zip'],
            city=data['city'],
            phone=data['phone'],
            mail=data['mail'],
            bic=data['bic'],
            iban=data['iban'],
            mail_tag=Tag.from_dict(data.get('mail_tag')),
            file_tag=Tag.from_dict(data.get('file_tag')),
            badge_tag=Tag.from_dict(data.get('badge_tag'))        ) 

@dataclass
class Sender:
    title: str
    firstname: str
    name: str
    street: str
    zip: str 
    city: str
    phone: str
    mail: str
    organisation: str
    id: int | None = None

    @property
    def label(self) -> str:
        result = ' '.join([self.title, self.firstname, self.name]).strip()
        if result and self.organisation:
            return f"{result} ({self.organisation})".strip()
        elif result:
            return result.strip()
        else:
            return self.organisation.strip()

@dataclass
class Animator:
    title: str
    firstname: str
    name: str
    street: str
    zip: str 
    city: str
    phone: str
    mail: str
    id: int | None = None

    @property
    def label(self) -> str:
        return ' '.join([self.title, self.firstname, self.name]).strip()

@dataclass
class Addressee:
    title: str
    firstname: str
    name: str
    street: str
    zip: str 
    city: str
    phone: str
    mail: str
    id: int | None = None

    @property
    def label(self) -> str:
        return ' '.join([self.title, self.firstname, self.name]).strip()

@dataclass
class Participant:
    title: str
    firstname: str
    name: str
    street: str
    zip: str 
    city: str
    phone: str
    mail: str
    sender_label: str | None = None

@dataclass
class Promotion:
    year: int
    year_fee: float
    participants: list[Participant] | None

    def __str__(self) -> str:
        return f"{self.year} - {self.year + 2}"    

    @classmethod
    def from_dict(cls, data: dict) -> 'Promotion':
        participants = data.get('participants') or []
        return cls(
            year=data['year'],
            year_fee=data['year_fee'],
            participants=[Participant(**p) for p in participants],
        )    

