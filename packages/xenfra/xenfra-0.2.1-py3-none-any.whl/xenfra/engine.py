# src/xenfra/engine.py

import os
import time
from pathlib import Path
import digitalocean
import fabric
from dotenv import load_dotenv
from sqlmodel import Session

# Xenfra modules
from . import dockerizer
from . import recipes
from .db.models import Project
from .db.session import get_session

class DeploymentError(Exception):
    """Custom exception for deployment failures."""
    def __init__(self, message, stage="Unknown"):
        self.message = message
        self.stage = stage
        super().__init__(f"Deployment failed at stage '{stage}': {message}")

class InfraEngine:
    """
    The InfraEngine is the core of Xenfra. It handles all interactions
    with the cloud provider and orchestrates the deployment lifecycle.
    """
    def __init__(self, token: str = None, db_session: Session = None):
        """
        Initializes the engine and validates the API token.
        """
        load_dotenv()
        self.token = token or os.getenv("DIGITAL_OCEAN_TOKEN")
        self.db_session = db_session or next(get_session())

        if not self.token:
            raise ValueError("DigitalOcean API token not found. Please set the DIGITAL_OCEAN_TOKEN environment variable.")
        try:
            self.manager = digitalocean.Manager(token=self.token)
            self.get_user_info()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to DigitalOcean: {e}")

    def _get_connection(self, ip_address: str):
        """Establishes a Fabric connection to the server."""
        private_key_path = str(Path.home() / ".ssh" / "id_rsa")
        if not Path(private_key_path).exists():
            raise DeploymentError("No private SSH key found at ~/.ssh/id_rsa.", stage="Setup")

        return fabric.Connection(
            host=ip_address,
            user="root",
            connect_kwargs={"key_filename": [private_key_path]},
        )

    def get_user_info(self):
        """Retrieves user account information."""
        return self.manager.get_account()

    def list_servers(self):
        """Retrieves a list of all Droplets."""
        return self.manager.get_all_droplets()

    def destroy_server(self, droplet_id: int, db_session: Session = None):
        """Destroys a Droplet by its ID and removes it from the local DB."""
        session = db_session or self.db_session
        
        # Find the project in the local DB
        project_to_delete = session.query(Project).filter(Project.droplet_id == droplet_id).first()

        # Destroy the droplet on DigitalOcean
        droplet = digitalocean.Droplet(token=self.token, id=droplet_id)
        droplet.destroy()

        # If it was in our DB, delete it
        if project_to_delete:
            session.delete(project_to_delete)
            session.commit()

    def list_projects_from_db(self, db_session: Session = None):
        """Lists all projects from the local database."""
        session = db_session or self.db_session
        return session.query(Project).all()

    def sync_with_provider(self, db_session: Session = None):
        """Reconciles the local database with the live state from DigitalOcean."""
        session = db_session or self.db_session
        
        # 1. Get live and local states
        live_droplets = self.manager.get_all_droplets(tag_name="xenfra")
        local_projects = self.list_projects_from_db(session)

        live_map = {d.id: d for d in live_droplets}
        local_map = {p.droplet_id: p for p in local_projects}

        # 2. Reconcile
        # Add new servers found on DO to our DB
        for droplet_id, droplet in live_map.items():
            if droplet_id not in local_map:
                new_project = Project(
                    droplet_id=droplet.id, name=droplet.name, ip_address=droplet.ip_address,
                    status=droplet.status, region=droplet.region['slug'], size=droplet.size_slug
                )
                session.add(new_project)

        # Remove servers from our DB that no longer exist on DO
        for project_id, project in local_map.items():
            if project_id not in live_map:
                session.delete(project)
        
        session.commit()
        return self.list_projects_from_db(session)

    def stream_logs(self, droplet_id: int, db_session: Session = None):
        """
        Verifies a server exists and streams its logs in real-time.
        """
        session = db_session or self.db_session
        
        # 1. Find project in local DB
        project = session.query(Project).filter(Project.droplet_id == droplet_id).first()
        if not project:
            raise DeploymentError(f"Project with Droplet ID {droplet_id} not found in local database.", stage="Log Streaming")

        # 2. Just-in-Time Verification
        try:
            droplet = self.manager.get_droplet(droplet_id)
        except digitalocean.baseapi.DataReadError as e:
            if e.response.status_code == 404:
                # The droplet doesn't exist, so remove it from our DB
                session.delete(project)
                session.commit()
                raise DeploymentError(f"Server '{project.name}' (ID: {droplet_id}) no longer exists on DigitalOcean. It has been removed from your local list.", stage="Log Streaming")
            else:
                raise e
        
        # 3. Stream logs
        ip_address = droplet.ip_address
        with self._get_connection(ip_address) as conn:
            conn.run("cd /root/app && docker-compose logs -f app", pty=True)



    def _ensure_ssh_key(self, logger):
        """Ensures a local public SSH key is on DigitalOcean."""
        pub_key_path = Path.home() / ".ssh" / "id_rsa.pub"
        if not pub_key_path.exists():
            raise DeploymentError("No SSH key found at ~/.ssh/id_rsa.pub. Please generate one.", stage="Setup")
        
        with open(pub_key_path) as f:
            pub_key_content = f.read()

        existing_keys = self.manager.get_all_sshkeys()
        for key in existing_keys:
            if key.public_key.strip() == pub_key_content.strip():
                logger("   - Found existing SSH key on DigitalOcean.")
                return key

        logger("   - No matching SSH key found. Creating a new one on DigitalOcean...")
        key = digitalocean.SSHKey(token=self.token, name="xenfra-cli-key", public_key=pub_key_content)
        key.create()
        return key

    def deploy_server(self, name: str, region: str, size: str, image: str, logger: callable, db_session: Session = None, **kwargs):
        """A stateful, blocking orchestrator for deploying a new server."""
        droplet = None
        session = db_session or self.db_session
        try:
            # === 1. SETUP STAGE ===
            logger("\n[bold blue]PHASE 1: SETUP[/bold blue]")
            ssh_key = self._ensure_ssh_key(logger)

            # === 2. ASSET GENERATION STAGE ===
            logger("\n[bold blue]PHASE 2: GENERATING DEPLOYMENT ASSETS[/bold blue]")
            context = {**kwargs} # Pass db config, etc.
            files = dockerizer.generate_templated_assets(context)
            for file in files:
                logger(f"   - Generated {file}")

            # === 3. CLOUD-INIT STAGE ===
            logger("\n[bold blue]PHASE 3: CREATING SERVER SETUP SCRIPT[/bold blue]")
            cloud_init_script = recipes.generate_stack(context)
            logger("   - Generated cloud-init script.")

            # === 4. DROPLET CREATION STAGE ===
            logger("\n[bold blue]PHASE 4: PROVISIONING SERVER[/bold blue]")
            droplet = digitalocean.Droplet(
                token=self.token, name=name, region=region, image=image, size_slug=size,
                ssh_keys=[ssh_key], userdata=cloud_init_script, tags=["xenfra"]
            )
            droplet.create()
            logger(f"   - Droplet '{name}' creation initiated (ID: {droplet.id}). Waiting for it to become active...")

            # === 5. POLLING STAGE ===
            logger("\n[bold blue]PHASE 5: WAITING FOR SERVER SETUP[/bold blue]")
            while True:
                droplet.load()
                if droplet.status == 'active':
                    logger("   - Droplet is active. Waiting for SSH to be available...")
                    break
                time.sleep(10)

            ip_address = droplet.ip_address

            # Retry SSH connection
            conn = None
            max_retries = 12 # 2-minute timeout for SSH
            for i in range(max_retries):
                try:
                    logger(f"   - Attempting SSH connection ({i+1}/{max_retries})...")
                    conn = self._get_connection(ip_address)
                    conn.open() # Explicitly open the connection
                    logger("   - SSH connection established.")
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        logger(f"   - SSH connection failed. Retrying in 10s...")
                        time.sleep(10)
                    else:
                        raise DeploymentError(f"Failed to establish SSH connection: {e}", stage="Polling")

            if not conn or not conn.is_connected:
                raise DeploymentError("Could not establish SSH connection.", stage="Polling")

            with conn:
                for i in range(30): # 5-minute timeout for cloud-init
                    if conn.run("test -f /root/setup_complete", warn=True).ok:
                        logger("   - Cloud-init setup complete.")
                        break
                    time.sleep(10)
                else:
                    raise DeploymentError("Server setup script failed to complete in time.", stage="Polling")

            # === 6. CODE UPLOAD STAGE ===
            logger("\n[bold blue]PHASE 6: UPLOADING APPLICATION CODE[/bold blue]")
            with self._get_connection(ip_address) as conn:
                fabric.transfer.Transfer(conn).upload(".", "/root/app", exclude=[".git", ".venv", "__pycache__"])
            logger("   - Code upload complete.")

            # === 7. FINAL DEPLOY STAGE ===
            logger("\n[bold blue]PHASE 7: BUILDING AND DEPLOYING CONTAINERS[/bold blue]")
            with self._get_connection(ip_address) as conn:
                result = conn.run("cd /root/app && docker-compose up -d --build", hide=True)
                if result.failed:
                    raise DeploymentError(f"docker-compose failed: {result.stderr}", stage="Deploy")
            logger("   - Docker containers are building in the background...")

            # === 8. VERIFICATION STAGE ===
            logger("\n[bold blue]PHASE 8: VERIFYING DEPLOYMENT[/bold blue]")
            app_port = context.get('port', 8000)
            for i in range(24): # 2-minute timeout for health checks
                logger(f"   - Health check attempt {i+1}/24...")
                with self._get_connection(ip_address) as conn:
                    # Check if container is running
                    ps_result = conn.run("cd /root/app && docker-compose ps", hide=True)
                    if "running" not in ps_result.stdout:
                        time.sleep(5)
                        continue
                    
                    # Check if application is responsive
                    curl_result = conn.run(f"curl -s --fail http://localhost:{app_port}/", warn=True)
                    if curl_result.ok:
                        logger("[bold green]   - Health check passed! Application is live.[/bold green]")
                        
                        # === 9. PERSISTENCE STAGE ===
                        logger("\n[bold blue]PHASE 9: SAVING DEPLOYMENT TO DATABASE[/bold blue]")
                        project = Project(
                            droplet_id=droplet.id,
                            name=droplet.name,
                            ip_address=ip_address,
                            status=droplet.status,
                            region=droplet.region['slug'],
                            size=droplet.size_slug,
                        )
                        session.add(project)
                        session.commit()
                        logger("   - Deployment saved.")

                        return droplet # Return the full droplet object
                time.sleep(5)
            else:
                # On failure, get logs and destroy droplet
                with self._get_connection(ip_address) as conn:
                    logs = conn.run("cd /root/app && docker-compose logs", hide=True).stdout
                raise DeploymentError(f"Application failed to become healthy in time. Logs:\n{logs}", stage="Verification")

        except Exception as e:
            if droplet:
                logger(f"[bold red]Deployment failed. The server '{droplet.name}' will NOT be cleaned up for debugging purposes.[/bold red]")
                # droplet.destroy() # Commented out for debugging
            raise e