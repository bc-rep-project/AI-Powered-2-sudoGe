from datetime import datetime
from pydantic import BaseModel, Field

class InteractionCreate(BaseModel):
    movieId_ml: str
    type: str
    value: int

class InteractionResponse(BaseModel):
    id: str = Field(alias="_id")
    userId: str
    movieId_ml: str
    type: str
    value: int
    timestamp: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True