from pydantic import BaseModel


class Token(BaseModel):
    api_key: str
    token_type: str


class User(BaseModel):
    email: str
