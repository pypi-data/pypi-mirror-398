from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware # Import SessionMiddleware
from fastapi.security import OAuth2PasswordBearer # This will be removed, as oauth2_scheme is in dependencies
from sqlmodel import Session, select
from jose import JWTError
from typing import List
from datetime import datetime

import os # Keep os import for now as it is used in other places.

from xenfra.engine import InfraEngine
from xenfra.models import Deployment, ProjectRead # Import ProjectRead
from xenfra.db.session import create_db_and_tables, get_session
from xenfra.db.models import User, UserRead, Credential, CredentialRead
from xenfra.security import decode_token, decrypt_token
from xenfra.dependencies import get_current_user, get_current_active_user, oauth2_scheme # Import oauth2_scheme from dependencies
from pydantic import BaseModel
from xenfra.config import settings


# --- Lifespan ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# --- App Initialization ---
app = FastAPI(
    title="Xenfra API",
    description="API for the Xenfra deployment engine.",
    version="0.1.0",
    lifespan=lifespan
)

# --- Middleware ---
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY) # Use settings.SECRET_KEY here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. In prod, strict listing.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router Imports (Moved after app initialization) ---
from xenfra.api import auth, connections, webhooks, billing

# --- Routers ---
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(connections.router, prefix="/connections", tags=["Connections"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(billing.router, prefix="/billing", tags=["Billing"])


# --- Models for Frontend Requests ---
class DeploymentCreateRequest(BaseModel):
    name: str
    region: str
    size: str
    image: str
    email: str
    domain: str | None = None
    repo_url: str | None = None # For future Git deployments via web UI


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Xenfra API"}

@app.post("/deployments/new")
def create_new_deployment(
    request: DeploymentCreateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user)
):
    """
    Triggers a new deployment based on provided configuration.
    """
    do_credential = session.exec(
        select(Credential).where(Credential.user_id == user.id, Credential.service == "digitalocean")
    ).first()
    
    if not do_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DigitalOcean credential not found for this user. Please connect your account.",
        )

    try:
        do_token = decrypt_token(do_credential.encrypted_token)
        engine = InfraEngine(token=do_token)
        
        # Offload the deployment to a background task
        background_tasks.add_task(
            engine.deploy_server,
            name=request.name,
            region=request.region,
            size=request.size,
            image=request.image,
            email=request.email,
            domain=request.domain,
            repo_url=request.repo_url
        )
        return {"status": "success", "message": "Deployment initiated in background."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {e}",
        )

@app.get("/users/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Fetch the current logged in user.
    """
    return current_user

@app.get("/users/me/connections", response_model=List[CredentialRead])
def read_user_connections(current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)):
    """
    Fetch the current logged in user's connected credentials (GitHub, DigitalOcean).
    """
    credentials = session.exec(select(Credential).where(Credential.user_id == current_user.id)).all()
    return credentials

@app.get("/projects", response_model=List[ProjectRead])
def list_projects(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user)
):
    """
    Lists Xenfra-managed Droplets as projects.
    """
    do_credential = session.exec(
        select(Credential).where(Credential.user_id == user.id, Credential.service == "digitalocean")
    ).first()
    
    if not do_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DigitalOcean credential not found for this user. Please connect your account.",
        )
    
    try:
        do_token = decrypt_token(do_credential.encrypted_token)
        engine = InfraEngine(token=do_token)
        
        droplets = engine.list_servers()
        projects = []
        for droplet in droplets:
            # For V0, a "project" is simply a Xenfra-managed Droplet
            # We filter by name convention 'xenfra-'
            if droplet.name.startswith("xenfra-"):
                estimated_monthly_cost = droplet.size['price_monthly'] if droplet.size else None
                projects.append(ProjectRead(
                    id=droplet.id,
                    name=droplet.name,
                    ip_address=droplet.ip_address,
                    status=droplet.status,
                    region=droplet.region['slug'],
                    size_slug=droplet.size['slug'],
                    estimated_monthly_cost=estimated_monthly_cost,
                    created_at=datetime.fromisoformat(droplet.created_at.replace('Z', '+00:00')) # Ensure datetime is timezone aware
                ))
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects from DigitalOcean: {e}",
        )