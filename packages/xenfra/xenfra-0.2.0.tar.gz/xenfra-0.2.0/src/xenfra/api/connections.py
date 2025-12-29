# src/xenfra/api/connections.py

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
import secrets

from xenfra.db.session import get_session
from xenfra.db.models import User, Credential, CredentialCreate
from xenfra.dependencies import get_current_active_user # Corrected import
from xenfra.security import encrypt_token
from xenfra.config import settings

router = APIRouter()

# --- GitHub OAuth ---
# GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID") # Moved inside function
# GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET") # Moved inside function
# GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/connections/github/callback") # Moved inside function

@router.get("/github/login")
def github_login(request: Request): # Add request: Request
    """Redirects the user to GitHub for authorization."""
    GITHUB_CLIENT_ID = settings.GITHUB_CLIENT_ID
    GITHUB_REDIRECT_URI = settings.GITHUB_REDIRECT_URI
    
    state = secrets.token_urlsafe(32)
    request.session["github_oauth_state"] = state
    
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=repo%20user:email&redirect_uri={GITHUB_REDIRECT_URI}&state={state}",
        status_code=302
    )

@router.get("/github/callback")
async def github_callback(code: str, request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_active_user)):
    """
    Handles the callback from GitHub, exchanges the code for a token,
    and stores the encrypted token.
    """
    received_state = request.query_params.get("state")
    stored_state = request.session.pop("github_oauth_state", None)

    if not received_state or not stored_state or received_state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Possible CSRF attack.")

    GITHUB_CLIENT_ID = settings.GITHUB_CLIENT_ID
    GITHUB_CLIENT_SECRET = settings.GITHUB_CLIENT_SECRET
    if not GITHUB_CLIENT_SECRET: # Explicit check for client secret
        raise HTTPException(status_code=500, detail="GitHub client secret not configured.")
    # GITHUB_REDIRECT_URI is not needed here
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            json={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
            headers={"Accept": "application/json"}
        )
    
    token_data = await token_response.json() # Await the json() coroutine
    access_token = token_data.get("access_token")

    if not access_token:
        # GitHub might return an error in token_data, e.g., {'error': 'bad_verification_code'}
        error_detail = token_data.get("error_description", token_data.get("error", "Unknown error during token exchange"))
        raise HTTPException(status_code=400, detail=f"Could not fetch GitHub access token: {error_detail}")

    # Encrypt and store the token
    encrypted_token = encrypt_token(access_token)

    # Fetch GitHub App installation ID
    async with httpx.AsyncClient() as client:
        installations_response = await client.get(
            "https://api.github.com/user/installations",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
    installations_data = await installations_response.json()
    installation_id = None
    if installations_data and "installations" in installations_data and len(installations_data["installations"]) > 0:
        installation_id = installations_data["installations"][0]["id"]
    
    new_credential = CredentialCreate(
        service="github", 
        encrypted_token=encrypted_token, 
        user_id=user.id, 
        github_installation_id=installation_id
    )
    db_credential = Credential.model_validate(new_credential)
    session.add(db_credential)
    session.commit()

    # Redirect user back to the frontend (URL should be configurable)
    return RedirectResponse(url=f"{settings.FRONTEND_OAUTH_REDIRECT_SUCCESS}?success=github", status_code=302)


# --- DigitalOcean OAuth ---
# DO_CLIENT_ID = os.getenv("DO_CLIENT_ID") # Moved inside function
# DO_CLIENT_SECRET = os.getenv("DO_CLIENT_SECRET") # Moved inside function
# DO_REDIRECT_URI = os.getenv("DO_REDIRECT_URI", "http://localhost:8000/connections/digitalocean/callback") # Moved inside function

@router.get("/digitalocean/login")
def digitalocean_login(request: Request): # Add request: Request
    """Redirects the user to DigitalOcean for authorization."""
    DO_CLIENT_ID = settings.DO_CLIENT_ID
    DO_REDIRECT_URI = settings.DO_REDIRECT_URI
        
    state = secrets.token_urlsafe(32)
    request.session["digitalocean_oauth_state"] = state

    return RedirectResponse(
        f"https://cloud.digitalocean.com/v1/oauth/authorize?client_id={DO_CLIENT_ID}&response_type=code&scope=read%20write&redirect_uri={DO_REDIRECT_URI}&state={state}",
        status_code=302
    )

@router.get("/digitalocean/callback")
async def digitalocean_callback(code: str, request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_active_user)):
    """
    Handles the callback from DigitalOcean, exchanges the code for a token,
    and stores the encrypted token.
    """
    received_state = request.query_params.get("state")
    stored_state = request.session.pop("digitalocean_oauth_state", None)

    if not received_state or not stored_state or received_state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Possible CSRF attack.")

    DO_CLIENT_ID = settings.DO_CLIENT_ID
    DO_CLIENT_SECRET = settings.DO_CLIENT_SECRET
    DO_REDIRECT_URI = settings.DO_REDIRECT_URI
    if not DO_CLIENT_SECRET: # Explicit check for client secret
        raise HTTPException(status_code=500, detail="DigitalOcean client secret not configured.")
    
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://cloud.digitalocean.com/v1/oauth/token",
            params={
                "grant_type": "authorization_code",
                "client_id": DO_CLIENT_ID,
                "client_secret": DO_CLIENT_SECRET,
                "code": code,
                "redirect_uri": DO_REDIRECT_URI
            }
        )

    token_data = await token_response.json() # Await the json() coroutine
    access_token = token_data.get("access_token")

    if not access_token:
        error_detail = token_data.get("error_description", token_data.get("error", "Unknown error during token exchange"))
        raise HTTPException(status_code=400, detail=f"Could not fetch DigitalOcean access token: {error_detail}")

    encrypted_token = encrypt_token(access_token)
    new_credential = CredentialCreate(service="digitalocean", encrypted_token=encrypted_token, user_id=user.id)
    db_credential = Credential.model_validate(new_credential)
    session.add(db_credential)
    session.commit()
    
    return RedirectResponse(url=f"{settings.FRONTEND_OAUTH_REDIRECT_SUCCESS}?success=digitalocean", status_code=302)
