from pydantic import BaseModel
from users.models import User


class Loot(BaseModel):
    item: str
    quantity: float


class LootWithParticipants(BaseModel):
    loot: Loot
    participants: list[User]
    cycle_id: int
