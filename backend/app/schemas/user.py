from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Public registration. Admin accounts can never be created here (FR-UM-07)."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["donor", "recipient"]


class AdminCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class DonorProfileIn(BaseModel):
    business_name: str = Field(min_length=1)
    business_type: str | None = None
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class DonorProfileOut(DonorProfileIn):
    model_config = ConfigDict(from_attributes=True)


class RecipientProfileIn(BaseModel):
    organisation_name: str = Field(min_length=1)
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    capacity_units: int = Field(gt=0)
    storage_types: list[str] = Field(min_length=1)
    accepted_categories: list[str] = Field(min_length=1)
    open_from: time | None = None
    open_to: time | None = None
    need_level: int = Field(default=3, ge=1, le=5)


class RecipientProfileOut(RecipientProfileIn):
    model_config = ConfigDict(from_attributes=True)

    verified: bool


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: Literal["donor", "recipient", "admin"]
    is_active: bool
    email_verified: bool


class EmailVerifyIn(BaseModel):
    token: str


class ResendVerificationIn(BaseModel):
    email: EmailStr


class MessageOut(BaseModel):
    message: str


class MeOut(UserOut):
    donor_profile: DonorProfileOut | None = None
    recipient_profile: RecipientProfileOut | None = None


class ActiveUpdate(BaseModel):
    is_active: bool
