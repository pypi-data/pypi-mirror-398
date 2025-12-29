# src/xenfra/api/webhooks.py

import hmac
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlmodel import Session, select

from xenfra.db.session import get_session
from xenfra.db.models import User, Credential
from xenfra.dependencies import get_current_active_user # Corrected import
from xenfra.engine import InfraEngine
from xenfra.security import decrypt_token
from xenfra.config import settings

router = APIRouter()

# This secret should be configured in your GitHub App's webhook settings
GITHUB_WEBHOOK_SECRET = settings.GITHUB_WEBHOOK_SECRET

async def verify_github_signature(request: Request):
    """
    Verify that the incoming webhook request is genuinely from GitHub.
    """
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="GitHub webhook secret not configured.")

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=400, detail="X-Hub-Signature-256 header is missing.")

    signature_parts = signature_header.split("=", 1)
    if len(signature_parts) != 2 or signature_parts[0] != "sha256":
        raise HTTPException(status_code=400, detail="Invalid signature format.")

    signature = signature_parts[1]
    body = await request.body()
    
    expected_signature = hmac.new(
        key=GITHUB_WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature.")


@router.post("/github", dependencies=[Depends(verify_github_signature)])
async def github_webhook(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Handles incoming webhooks from GitHub to manage Preview Environments.
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "pull_request":
        action = payload.get("action")
        pr_info = payload.get("pull_request", {})
        repo_info = payload.get("repository", {})
        
        repo_full_name = repo_info.get("full_name")
        pr_number = pr_info.get("number")
        commit_sha = pr_info.get("head", {}).get("sha")
        clone_url = repo_info.get("clone_url")
        installation_id = payload.get("installation", {}).get("id")

        if not all([repo_full_name, pr_number, commit_sha, clone_url, installation_id]):
            raise HTTPException(status_code=400, detail="Incomplete pull request payload or missing installation ID.")

        # Find the user associated with this GitHub App installation
        github_credential = session.exec(
            select(Credential).where(
                Credential.service == "github",
                Credential.github_installation_id == installation_id
            )
        ).first()

        if not github_credential:
            raise HTTPException(status_code=404, detail=f"No GitHub credential found for installation ID {installation_id}.")

        user = session.exec(select(User).where(User.id == github_credential.user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found for credential with installation ID {installation_id}.")

        # Find the user's DigitalOcean credential
        do_credential = session.exec(
            select(Credential).where(Credential.user_id == user.id, Credential.service == "digitalocean")
        ).first()
        
        if not do_credential:
            raise HTTPException(status_code=400, detail=f"No DigitalOcean credential found for user {user.email}.")

        # Decrypt the token and instantiate the engine
        try:
            do_token = decrypt_token(do_credential.encrypted_token)
            engine = InfraEngine(token=do_token) # InfraEngine needs to be adapted to accept a token
            
            print(f"DEBUG(WEBHOOKS): engine object id: {id(engine)}, type: {type(engine)}")
            print(f"DEBUG(WEBHOOKS): engine.list_servers method id: {id(engine.list_servers)}, type: {type(engine.list_servers)}")

        except Exception as e:
            return {"status": "error", "detail": f"Failed to initialize engine: {e}"}

        server_name = f"xenfra-pr-{repo_full_name.replace('/', '-')}-{pr_number}"

        if action in ["opened", "synchronize"]:
            print(f"🚀 Deploying preview for PR #{pr_number} from {repo_full_name} at {commit_sha[:7]}")
            # This should be run in a background task in a real app
            background_tasks.add_task(
                engine.deploy_server,
                name=server_name,
                region="nyc3", # Using a default for now
                size="s-1vcpu-1gb", # Using a default for now
                image="ubuntu-22-04-x64", # Using a default for now
                email=user.email,
                repo_url=clone_url,
                commit_sha=commit_sha
            )
            # TODO: Post comment back to GitHub with the preview URL
            # TODO: Store the droplet_id and PR number association in the DB
            
            return {"status": "success", "action": "deploying in background"}


        elif action == "closed":
            print(f"🔥 Destroying preview for closed PR #{pr_number} from {repo_full_name}")
            try:
                # Find the droplet associated with this PR
                servers = engine.list_servers()
                droplet_to_destroy = None
                for s in servers:
                    if s.name == server_name:
                        droplet_to_destroy = s
                        break

                if droplet_to_destroy:
                    background_tasks.add_task(engine.destroy_server, droplet_to_destroy.id)
                    print(f"✅ Droplet {droplet_to_destroy.name} ({droplet_to_destroy.id}) scheduled for destruction.")
                else:
                    print(f"⚠️ No droplet found with name {server_name} to destroy.")
            except Exception as e:
                print(f"❌ Failed to destroy preview environment: {e}")

            return {"status": "success", "action": "destroying in background"}

    return {"status": "success", "detail": "Webhook received"}
