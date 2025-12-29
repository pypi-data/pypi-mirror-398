# src/xenfra/api/billing.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from xenfra.db.session import get_session
from xenfra.db.models import User, Credential
from xenfra.dependencies import get_current_active_user # Corrected import
from xenfra.engine import InfraEngine
from xenfra.security import decrypt_token
from xenfra.models import DropletCostRead # Import new model

router = APIRouter()

class BalanceRead(BaseModel):
    month_to_date_balance: str
    account_balance: str
    month_to_date_usage: str
    generated_at: str
    error: str | None = None

@router.get("/balance", response_model=BalanceRead)
def get_billing_balance(
    session: Session = Depends(get_session), 
    user: User = Depends(get_current_active_user)
):
    """
    Get the current DigitalOcean account balance and month-to-date usage.
    """
    # Find the user's DigitalOcean credential
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
        balance_data = engine.get_account_balance()
        return BalanceRead(**balance_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch balance from DigitalOcean: {e}",
        )

@router.get("/droplets", response_model=list[DropletCostRead])
def get_billing_droplets(
    session: Session = Depends(get_session), 
    user: User = Depends(get_current_active_user)
):
    """
    Get a list of Xenfra-managed DigitalOcean droplets with their estimated monthly costs.
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
        droplets_data = engine.get_droplet_cost_estimates()
        return [DropletCostRead(**d) for d in droplets_data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch droplet cost estimates from DigitalOcean: {e}",
        )
