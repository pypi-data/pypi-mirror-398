import click
import os
import sys
import subprocess
import threading
import signal
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from .generator import generate_project

console = Console()

LOGO = r"""
╔═══════════════════════════════════════════════════════════════╗
║    ____    _                            _    __               ║
║   / __ \  (_)___ _____  ____ _____     | |  / /_  _____       ║
║  / / / / / / __ `/ __ \/ __ `/ __ \    | | / / / / / _ \      ║
║ / /_/ / / / /_/ / / / / /_/ / /_/ /    | |/ / /_/ /  __/      ║
║/_____/_/ /\__,_/_/ /_/\__, /\____/     |___/\__,_/\___/       ║
║     /___/            /____/                                   ║
║      Django + Vue.js Project Generator By Abdulla Fajal       ║
╚═══════════════════════════════════════════════════════════════╝
"""


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version='1.1.2', prog_name='django-vue-start')
def cli(ctx):
    """
    🚀 Django + Vue.js Project Generator
    
    Generate a production-ready full-stack application with Django backend
    and Vue.js frontend, complete with authentication, Docker, and CI/CD.
    
    Commands:
      new     Create a new project (default if no command given)
      run     Run development servers
    """
    if ctx.invoked_subcommand is None:
        # Default to 'new' command behavior if no subcommand
        ctx.invoke(new)


@cli.command()
@click.argument('name', required=False)
@click.option('--database', type=click.Choice(['sqlite', 'postgresql', 'mysql']), 
              help='Database backend')
@click.option('--auth', type=click.Choice(['jwt', 'session']), 
              help='Authentication type')
@click.option('--celery/--no-celery', default=None, 
              help='Include Celery for background tasks')
@click.option('--allauth/--no-allauth', default=None, 
              help='Include Django Allauth for social auth')
@click.option('--skip-prompts', is_flag=True, 
              help='Skip interactive prompts and use defaults')
def new(name, database, auth, celery, allauth, skip_prompts):
    """Create a new Django + Vue.js project."""
    console.print(LOGO, style="bold cyan")
    
    # Project name
    if not name:
        if skip_prompts:
            name = "my_project"
        else:
            name = Prompt.ask(
                "[bold]Project name[/bold]",
                default="my_project"
            )
    
    # Validate project name
    if not name.replace("_", "").replace("-", "").isalnum():
        console.print("[bold red]Error:[/bold red] Project name must be alphanumeric (underscores and hyphens allowed)")
        sys.exit(1)
    
    if os.path.exists(name):
        console.print(f"[bold red]Error:[/bold red] Directory '{name}' already exists.")
        sys.exit(1)
    
    # Database selection
    if database is None:
        if skip_prompts:
            database = "postgresql"
        else:
            database = Prompt.ask(
                "[bold]Database[/bold]",
                choices=["postgresql", "sqlite", "mysql"],
                default="sqlite"
            )
    
    # Auth type selection
    if auth is None:
        if skip_prompts:
            auth = "jwt"
        else:
            auth = Prompt.ask(
                "[bold]Authentication type[/bold]",
                choices=["jwt", "session"],
                default="jwt"
            )
    
    # Celery/Redis for background tasks
    if celery is None:
        if skip_prompts:
            celery = True
        else:
            celery = Confirm.ask(
                "[bold]Include Celery[/bold] for background tasks?",
                default=True
            )
    
    # Django Allauth for social authentication
    if allauth is None:
        if skip_prompts:
            allauth = True
        else:
            allauth = Confirm.ask(
                "[bold]Include Django Allauth[/bold] for social authentication?",
                default=True
            )
    
    # Show configuration summary
    console.print()
    table = Table(title="Project Configuration", show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Project Name", name)
    table.add_row("Database", database)
    table.add_row("Authentication", auth.upper())
    table.add_row("Celery (Background Tasks)", "✓" if celery else "✗")
    table.add_row("Django Allauth (Social Auth)", "✓" if allauth else "✗")
    console.print(table)
    console.print()
    
    if not skip_prompts:
        if not Confirm.ask("Proceed with this configuration?", default=True):
            console.print("[yellow]Aborted.[/yellow]")
            sys.exit(0)
    
    console.print(f"\n[bold]Creating project:[/bold] [cyan]{name}[/cyan]...")
    
    try:
        generate_project(
            project_name=name,
            database=database,
            auth_type=auth,
            include_celery=celery,
            include_allauth=allauth
        )
        
        console.print()
        console.print(Panel.fit(
            f"[bold green]✓ Successfully created project {name}![/bold green]\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  1. [cyan]cd {name}[/cyan]\n"
            f"  2. [cyan]django-vue-start run dev[/cyan]\n\n"
            f"[dim]Use --docker flag for Docker-based development[/dim]",
            title="🎉 Success",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[bold red]Error generating project:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('mode', type=click.Choice(['dev', 'backend', 'frontend', 'stop', 'migrate', 'shell']))
@click.option('--docker', is_flag=True, help='Use Docker instead of local development')
@click.option('--build', is_flag=True, help='Force rebuild containers (Docker only)')
def run(mode, docker, build):
    """
    Run development servers and manage the project.
    
    \b
    Modes:
      dev      Start development servers (backend + frontend)
      backend  Start only Django backend
      frontend Start only Vue frontend
      stop     Stop running servers
      migrate  Run database migrations
      shell    Open Django shell
    
    By default, runs locally without Docker.
    Use --docker flag for Docker-based development.
    """
    # Check if we're in a project directory
    if mode != 'stop' and (not os.path.exists('backend') or not os.path.exists('frontend')):
        console.print("[bold red]Error:[/bold red] Not in a project directory.")
        console.print("Make sure you're in a project directory created by django-vue-start.")
        sys.exit(1)
    
    if docker:
        _run_docker(mode, build)
    else:
        _run_local(mode)


def _get_venv_path():
    """Find the virtual environment path."""
    for path in ['backend/.venv', 'backend/venv', '.venv', 'venv']:
        if os.path.exists(path):
            return path
    return None


def _create_venv(has_uv):
    """Create a virtual environment and install dependencies."""
    console.print("[yellow]No virtual environment found. Creating one...[/yellow]")
    venv_path = 'backend/.venv'
    
    if has_uv:
        # Use uv for faster venv creation
        subprocess.run(['uv', 'venv', venv_path], check=True, cwd=os.getcwd())
        
        # Install requirements with uv - use --python to specify the venv's python
        python_in_venv = os.path.join(os.getcwd(), venv_path, 'bin', 'python')
        console.print("[yellow]Installing backend dependencies with uv (fast!)...[/yellow]")
        subprocess.run([
            'uv', 'pip', 'install', 
            '-r', 'backend/requirements.txt',
            '--python', python_in_venv
        ], check=True)
    else:
        # Fallback to standard venv + pip
        subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
        
        console.print("[yellow]Installing backend dependencies...[/yellow]")
        console.print("[dim]Tip: Install 'uv' for 10-100x faster installs: pip install uv[/dim]")
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        subprocess.run([pip_path, 'install', '-r', 'backend/requirements.txt'], check=True)
        
    return venv_path


def _kill_process_on_port(port):
    """Kill process listening on a specific port."""
    try:
        # Find PID using lsof
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}'],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split('\n')
        
        for pid in pids:
            if pid:
                subprocess.run(['kill', '-9', pid], check=False)
                return True
    except Exception:
        pass
    return False


def _run_local(mode):
    """Run development servers locally without Docker."""
    
    # Check if uv is available
    has_uv = subprocess.run(['which', 'uv'], capture_output=True).returncode == 0
    
    if mode == 'dev':
        console.print("[bold cyan]🚀 Starting local development servers...[/bold cyan]")
        console.print()
        
        # Ensure .env exists
        if not os.path.exists('backend/.env') and os.path.exists('backend/.env.example'):
            console.print("[yellow]Creating backend/.env from .env.example...[/yellow]")
            import shutil
            shutil.copy('backend/.env.example', 'backend/.env')
        
        # Setup venv
        venv_path = _get_venv_path()
        if not venv_path:
            venv_path = _create_venv(has_uv)
        
        python_path = os.path.abspath(os.path.join(venv_path, 'bin', 'python'))
        
        # Install frontend deps if needed
        if not os.path.exists('frontend/node_modules'):
            console.print("[yellow]Installing frontend dependencies...[/yellow]")
            subprocess.run(['npm', 'install'], cwd='frontend', check=True)
        
        console.print()
        console.print("  Backend:  [link=http://localhost:8000]http://localhost:8000[/link]")
        console.print("  Frontend: [link=http://localhost:5173]http://localhost:5173[/link]")
        console.print("  API Docs: [link=http://localhost:8000/api/docs/]http://localhost:8000/api/docs/[/link]")
        console.print()
        console.print("[dim]Press Ctrl+C to stop both servers[/dim]")
        
        # Start both servers
        backend_env = os.environ.copy()
        backend_env['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
        
        # Use preexec_fn=os.setsid to create new process group
        backend_process = subprocess.Popen(
            [python_path, 'manage.py', 'runserver', '0.0.0.0:8000'],
            cwd='backend',
            env=backend_env,
            preexec_fn=os.setsid
        )
        
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd='frontend',
            preexec_fn=os.setsid
        )
        
        def signal_handler(sig, frame):
            console.print("\n[yellow]Stopping servers...[/yellow]")
            try:
                os.killpg(os.getpgid(backend_process.pid), signal.SIGTERM)
            except:
                pass
            try:
                os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)
            except:
                pass
            console.print("[bold green]✓ Servers stopped.[/bold green]")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for processes
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            signal_handler(None, None)

    elif mode == 'backend':
        console.print("[bold cyan]🚀 Starting Django backend...[/bold cyan]")
        venv_path = _get_venv_path()
        if not venv_path:
            venv_path = _create_venv(has_uv)
            
        python_path = os.path.abspath(os.path.join(venv_path, 'bin', 'python'))
        backend_env = os.environ.copy()
        backend_env['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
        
        try:
            subprocess.run(
                [python_path, 'manage.py', 'runserver', '0.0.0.0:8000'],
                cwd='backend',
                env=backend_env
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping backend...[/yellow]")

    elif mode == 'frontend':
        console.print("[bold cyan]🚀 Starting Vue frontend...[/bold cyan]")
        if not os.path.exists('frontend/node_modules'):
            console.print("[yellow]Installing frontend dependencies...[/yellow]")
            subprocess.run(['npm', 'install'], cwd='frontend', check=True)
            
        try:
            subprocess.run(['npm', 'run', 'dev'], cwd='frontend')
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping frontend...[/yellow]")
            
    elif mode == 'stop':
        console.print("[bold cyan]Stopping local servers...[/bold cyan]")
        stopped_backend = _kill_process_on_port(8000)
        stopped_frontend = _kill_process_on_port(5173)
        
        if stopped_backend:
            console.print("[green]✓ Stopped backend (port 8000)[/green]")
        if stopped_frontend:
            console.print("[green]✓ Stopped frontend (port 5173)[/green]")
            
        if not stopped_backend and not stopped_frontend:
            console.print("[yellow]No servers found running on ports 8000 or 5173.[/yellow]")
        
    elif mode == 'migrate':
        console.print("[bold cyan]Running migrations...[/bold cyan]")
        
        venv_path = _get_venv_path()
        if not venv_path:
            console.print("[bold red]Error:[/bold red] No virtual environment found. Run 'django-vue-start run dev' first.")
            sys.exit(1)
        
        python_path = os.path.abspath(os.path.join(venv_path, 'bin', 'python'))
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
        
        result = subprocess.run(
            [python_path, 'manage.py', 'migrate'],
            cwd='backend',
            env=env
        )
        if result.returncode == 0:
            console.print("[bold green]✓ Migrations complete![/bold green]")
            
    elif mode == 'shell':
        console.print("[bold cyan]Opening Django shell...[/bold cyan]")
        
        venv_path = _get_venv_path()
        if not venv_path:
            console.print("[bold red]Error:[/bold red] No virtual environment found. Run 'django-vue-start run dev' first.")
            sys.exit(1)
        
        python_path = os.path.abspath(os.path.join(venv_path, 'bin', 'python'))
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
        
        subprocess.run(
            [python_path, 'manage.py', 'shell'],
            cwd='backend',
            env=env
        )


def _run_docker(mode, build):
    """Run development servers using Docker."""
    
    if not os.path.exists('docker-compose.yml'):
        console.print("[bold red]Error:[/bold red] No docker-compose.yml found.")
        sys.exit(1)
    
    if mode == 'dev':
        console.print("[bold cyan]🚀 Starting Docker development servers...[/bold cyan]")
        console.print()
        console.print("  Backend:  [link=http://localhost:8000]http://localhost:8000[/link]")
        console.print("  Frontend: [link=http://localhost:3000]http://localhost:3000[/link]")
        console.print("  API Docs: [link=http://localhost:8000/api/docs/]http://localhost:8000/api/docs/[/link]")
        console.print()
        
        # Ensure .env exists
        if not os.path.exists('backend/.env') and os.path.exists('backend/.env.example'):
            console.print("[yellow]Creating backend/.env from .env.example...[/yellow]")
            import shutil
            shutil.copy('backend/.env.example', 'backend/.env')
        
        cmd = ['docker', 'compose', 'up', '-d']
        if build:
            cmd.append('--build')
        
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            sys.exit(result.returncode)
        
        console.print()
        console.print("[bold green]✓ Development servers started![/bold green]")
        console.print("[dim]Run 'django-vue-start run logs --docker' to see output[/dim]")
        console.print("[dim]Run 'django-vue-start run stop --docker' to stop servers[/dim]")
        
    elif mode == 'stop':
        console.print("[bold cyan]Stopping containers...[/bold cyan]")
        subprocess.run(['docker', 'compose', 'down'])
        console.print("[bold green]✓ Containers stopped.[/bold green]")
        
    elif mode == 'migrate':
        console.print("[bold cyan]Running migrations...[/bold cyan]")
        result = subprocess.run([
            'docker', 'compose', 'exec', 'backend',
            'python', 'manage.py', 'migrate'
        ])
        if result.returncode == 0:
            console.print("[bold green]✓ Migrations complete![/bold green]")
            
    elif mode == 'shell':
        console.print("[bold cyan]Opening Django shell...[/bold cyan]")
        subprocess.run([
            'docker', 'compose', 'exec', 'backend',
            'python', 'manage.py', 'shell'
        ])


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
