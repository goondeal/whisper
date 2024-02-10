from typing import Literal
from datetime import datetime
from pydantic import BaseModel, validator, ValidationError


class UserBase(BaseModel):
    email: str
    name: str
    gender: Literal['M', 'F']
    

class UserCreate(UserBase):
    password: str

    @validator("password")
    def validate_password(cls, password, **kwargs):
        if not password or len(password) < 6:
            raise ValidationError('Password minimum length is 6')
        return password


class UserInfo(UserBase):
    bio: str | None = ''
    class Config:
        orm_mode = True

class PrivacySettings(BaseModel):
    allow_new_messages: bool
    allow_sending_images: bool
    allow_anonymous_users_messages: bool
    allow_notifications: bool
    hide_visitors_count: bool
    hide_last_seen: bool
    appear_in_search_results: bool

    class Config:
        orm_mode = True

class User(UserInfo, PrivacySettings):
    id: int
    # is_active: bool
    joined_at: datetime
    
    class Config:
        orm_mode = True

class UserSearchResult(UserInfo):
    id: int
    joined_at: datetime
    
    class Config:
        orm_mode = True


class MessageBase(BaseModel):
    content: str
    receiver_id: int
    is_anonymous: bool


class SentMessage(MessageBase):
    id: int
    is_seen: bool
    sent_at: datetime
    receiver: User


class MessageCreate(MessageBase):
    sender_id: int | None


class AnonymousMessage(MessageBase):
    id: int
    is_featured: bool
    is_public: bool
    is_seen: bool
    sent_at: datetime

    class Config:
        orm_mode = True

class Message(AnonymousMessage):
    sender_id: int | None = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
