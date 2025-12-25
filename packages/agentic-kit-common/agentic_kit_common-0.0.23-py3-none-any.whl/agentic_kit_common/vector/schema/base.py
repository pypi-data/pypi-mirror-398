from pydantic import BaseModel


class VectorBaseModel(BaseModel):
    uid: str

    score: float = 0
