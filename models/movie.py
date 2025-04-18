from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List

class MovieBase(BaseModel):
    movieId_ml: str
    title: str
    genres: str

class MovieResponse(MovieBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MovieListResponse(BaseModel):
    movies: List[MovieResponse]
    total: int