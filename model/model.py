from dataclasses import dataclass


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

    @classmethod
    def from_dict(cls, data: dict) -> 'Promotion':
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
            iban=data['iban']
        ) 

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

