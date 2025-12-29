import click
from rich.console import Console
from rich.table import Table

from xenfra.engine import InfraEngine
from xenfra import dockerizer
import yaml

console = Console()

@click.group()
@click.pass_context
def main(ctx):
    """
    Xenfra CLI: A 'Zen Mode' infrastructure engine for Python developers.
    """
    try:
        ctx.obj = {'engine': InfraEngine()}
        user_info = ctx.obj['engine'].get_user_info()
        console.print(f"[bold underline]Xenfra CLI[/bold underline] - Logged in as [green]{user_info.email}[/green]")
    except Exception as e:
        console.print(f"[bold red]CRITICAL ERROR:[/bold red] Failed to initialize engine: {e}")
        exit(1)

@main.command()
@click.pass_context
def init(ctx):
    """Initializes a project by creating a xenfra.yaml configuration file."""
    console.print("\n[bold blue]🔎 INITIALIZING PROJECT[/bold blue]")

    framework, _, _ = dockerizer.detect_framework()
    if not framework:
        console.print("[yellow]   Warning: No recognizable web framework detected.[/yellow]")

    console.print(f"   - Detected [cyan]{framework or 'unknown'}[/cyan] project.")

    use_db = click.confirm("\n   Would you like to add a PostgreSQL database to your deployment?", default=False)
    
    config = {
        'name': 'xenfra-app',
        'digitalocean': {
            'region': 'nyc3',
            'size': 's-1vcpu-1gb',
            'image': 'ubuntu-22-04-x64'
        },
        'app': {
            'framework': framework
        }
    }

    if use_db:
        config['database'] = {
            'type': 'postgres',
            'user': 'db_user',
            'password': 'db_password', # In a real scenario, this should be handled more securely
            'name': 'app_db'
        }
        console.print("   - Added [bold green]PostgreSQL[/bold green] to the configuration.")

    with open('xenfra.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print("\n[bold green]✅ SUCCESS![/bold green]")
    console.print("   - Created [cyan]xenfra.yaml[/cyan].")
    console.print("\n   Next step: Review the configuration and run 'xenfra deploy'!")


@main.command()
@click.pass_context
def deploy(ctx):
    """Deploys the project based on the xenfra.yaml configuration."""
    console.print("\n[bold green]🚀 INITIATING DEPLOYMENT FROM CONFIGURATION[/bold green]")
    
    try:
        with open('xenfra.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise click.ClickException("No 'xenfra.yaml' found. Run 'xenfra init' to create a configuration file.")

    engine = ctx.obj['engine']
    
    # Extract config values
    name = config.get('name', 'xenfra-app')
    do_config = config.get('digitalocean', {})
    region = do_config.get('region', 'nyc3')
    size = do_config.get('size', 's-1vcpu-1gb')
    image = do_config.get('image', 'ubuntu-22-04-x64')
    
    # Build context for templates
    template_context = {
        'database': config.get('database', {}).get('type'),
        'db_user': config.get('database', {}).get('user'),
        'db_password': config.get('database', {}).get('password'),
        'db_name': config.get('database', {}).get('name'),
        'email': ctx.obj['engine'].get_user_info().email
    }

    console.print(f"   - App Name: [cyan]{name}[/cyan]")
    console.print(f"   - Region: [cyan]{region}[/cyan], Size: [cyan]{size}[/cyan]")
    if template_context.get('database'):
        console.print(f"   - Including Database: [cyan]{template_context['database']}[/cyan]")

    if not click.confirm(f"\n   Ready to deploy '{name}' from 'xenfra.yaml'?"):
        return
        
    with console.status("[bold green]Deployment in progress...[/bold green]"):
        result = engine.deploy_server(
            name=name,
            region=region,
            size=size,
            image=image,
            logger=console.log,
            **template_context
        )
    
    console.print(f"\n[bold green]✅ DEPLOYMENT COMPLETE![/bold green]")
    console.print(result)

@main.command(name="list")
@click.option('--refresh', is_flag=True, help="Sync with the cloud provider before listing.")
@click.pass_context
def list_projects(ctx, refresh):
    """Lists all active Xenfra projects from the local database."""
    engine = ctx.obj['engine']
    
    if refresh:
        console.print("\n[bold]📡 SYNCING WITH CLOUD PROVIDER...[/bold]")
        with console.status("Calling DigitalOcean API and reconciling state..."):
            projects = engine.sync_with_provider()
    else:
        console.print("\n[bold]⚡️ LISTING PROJECTS FROM LOCAL DATABASE[/bold]")
        projects = engine.list_projects_from_db()
    
    if not projects:
        console.print("[yellow]   No active projects found. Run 'xenfra deploy' to create one.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Droplet ID", style="dim", width=12)
        table.add_column("Name", style="cyan")
        table.add_column("IP Address", style="green")
        table.add_column("Status")
        table.add_column("Region")
        table.add_column("Size")
        for p in projects:
            table.add_row(str(p.droplet_id), p.name, p.ip_address, p.status, p.region, p.size)
        console.print(table)

@main.command(name="logs")
@click.pass_context
def logs(ctx):
    """Streams real-time logs from a deployed project."""
    engine = ctx.obj['engine']
    
    console.print("\n[bold yellow]📡 SELECT A PROJECT TO STREAM LOGS[/bold yellow]")
    projects = engine.list_projects_from_db()

    if not projects:
        console.print("[yellow]   No active projects to stream logs from.[/yellow]")
        return

    project_map = {str(i+1): p for i, p in enumerate(projects)}
    for k, p in project_map.items():
        console.print(f"   [{k}] {p.name} ({p.ip_address})")

    choice_key = click.prompt("\n   Select Project (0 to cancel)", type=click.Choice(['0'] + list(project_map.keys())), show_choices=False)
    if choice_key == '0':
        return

    target = project_map[choice_key]
    
    try:
        console.print(f"\n[bold green]-- Attaching to logs for {target.name} (Press Ctrl+C to stop) --[/bold green]")
        engine.stream_logs(target.droplet_id)
    except DeploymentError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e.message}")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]-- Log streaming stopped by user. --[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


@main.command()
@click.pass_context
def destroy(ctx):
    """Destroys a deployed project."""
    engine = ctx.obj['engine']
    
    console.print("\n[bold red]🧨 SELECT A PROJECT TO DESTROY[/bold red]")
    projects = engine.list_projects_from_db()

    if not projects:
        console.print("[yellow]   No active projects to destroy.[/yellow]")
        return

    project_map = {str(i+1): p for i, p in enumerate(projects)}
    for k, p in project_map.items():
        console.print(f"   [{k}] {p.name} ({p.ip_address})")

    choice_key = click.prompt("\n   Select Project to DESTROY (0 to cancel)", type=click.Choice(['0'] + list(project_map.keys())), show_choices=False)
    if choice_key == '0':
        return
        
    target = project_map[choice_key]

    if click.confirm(f"   Are you SURE you want to permanently delete [red]{target.name}[/red] (Droplet ID: {target.droplet_id})? This action cannot be undone."):
        with console.status(f"💥 Destroying {target.name}..."):
            engine.destroy_server(target.droplet_id)
        console.print(f"[green]   Project '{target.name}' has been destroyed.[/green]")

if __name__ == "__main__":
    main()