from dataclasses import dataclass

from nicegui import ui

from controller.database_controller import database_controller
from model.model import Promotion


@dataclass(frozen=True)
class SessionState:
    promotion_id: int | None
    session_id: str
    name: str
    can_edit: bool = False

    @property
    def promotion(self) -> Promotion | None:
        return database_controller.get_promotion_by_id(self.promotion_id)
    