from nicegui import ui

from controller.database_controller import database_controller
from model.model import Promotion


class SessionState:
    def __init__(self, promotion_id: int | None):
        self.promotion_id = promotion_id
        self.session_id = ui.context.client.id

    @property
    def promotion(self) -> Promotion | None:
        return database_controller.get_promotion_by_id(self.promotion_id)
    