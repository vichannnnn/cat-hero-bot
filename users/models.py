from pydantic import BaseModel


class User(BaseModel):
    username: str
    discord_id: int
