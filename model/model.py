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


@dataclass
class Promotion:
    year: int
    year_fee: float
    information: Information | None

    @classmethod
    def from_dict(cls, data: dict) -> 'Promotion':
        info = data.get('information')
        return cls(
            year=data['year'],
            year_fee=data['year_fee'],
            information=Information(**info) if info else None,
        )    
