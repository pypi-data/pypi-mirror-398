# src/xenfra/db/models.py

from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    credentials: List["Credential"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

class CredentialBase(SQLModel):
    service: str # e.g., "digitalocean", "github"
    encrypted_token: str
    user_id: int = Field(foreign_key="user.id")
    github_installation_id: Optional[int] = Field(default=None, index=True)

class Credential(CredentialBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    user: User = Relationship(back_populates="credentials")

class CredentialCreate(CredentialBase):
    pass

class CredentialRead(SQLModel):
    id: int
    service: str
    user_id: int

# --- Project Model for CLI state ---

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    droplet_id: int = Field(unique=True, index=True)
    name: str
    ip_address: str
    status: str
    region: str
    size: str

