import os
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def generate_project(
    project_name: str,
    database: str = "postgresql",
    auth_type: str = "jwt",
    include_celery: bool = True,
    include_allauth: bool = True
):
    """
    Generates the project structure and renders templates.
    
    Args:
        project_name: Name of the project to create
        database: Database backend (postgresql, sqlite, mysql)
        auth_type: Authentication type (jwt, session)
        include_celery: Include Celery for background tasks
        include_allauth: Include Django Allauth for social auth
    """
    # Find templates directory
    base_dir = Path(__file__).resolve().parent
    
    # Try package templates first, then repo structure
    package_templates_dir = base_dir / "templates"
    repo_templates_dir = base_dir.parent.parent / "templates"
    
    if package_templates_dir.exists():
        templates_dir = package_templates_dir
    elif repo_templates_dir.exists():
        templates_dir = repo_templates_dir
    else:
        raise FileNotFoundError(
            f"Templates directory not found. Checked:\n"
            f"  - {package_templates_dir}\n"
            f"  - {repo_templates_dir}"
        )

    target_dir = Path(os.getcwd()) / project_name
    target_dir.mkdir(parents=True, exist_ok=False)

    # Setup Jinja2 with custom delimiters to avoid conflicts with Vue
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        variable_start_string='[[',
        variable_end_string=']]',
        block_start_string='[[%',
        block_end_string='%]]',
        comment_start_string='[[#',
        comment_end_string='#]]'
    )
    
    # Build context for template rendering
    project_slug = project_name.lower().replace(" ", "_").replace("-", "_")
    
    context = {
        "project_name": project_name,
        "project_slug": project_slug,
        "database": database,
        "auth_type": auth_type,
        "include_celery": include_celery,
        "include_allauth": include_allauth,
        # Computed values
        "use_postgres": database == "postgresql",
        "use_sqlite": database == "sqlite",
        "use_mysql": database == "mysql",
        "use_jwt": auth_type == "jwt",
        "use_session": auth_type == "session",
    }

    # Copy and render templates
    _copy_template_dir(templates_dir, target_dir, env, context)
    
    # Post-processing: Create empty directories if needed
    (target_dir / "backend" / "media").mkdir(exist_ok=True)
    (target_dir / "backend" / "staticfiles").mkdir(exist_ok=True)
    
    # Create .env file from example if it doesn't exist
    env_example = target_dir / "backend" / ".env.example"
    env_file = target_dir / "backend" / ".env"
    if env_example.exists() and not env_file.exists():
        shutil.copy2(env_example, env_file)


def _copy_template_dir(source: Path, dest: Path, env: Environment, context: dict):
    """
    Recursively copy and render template directory.
    """
    for item in source.iterdir():
        # Skip unwanted files/directories
        if item.name in ("__pycache__", ".DS_Store"):
            continue
        if item.name.startswith(".") and item.name not in (
            ".gitignore", ".env.example", ".env.local", ".env.test", 
            ".env.production", ".pre-commit-config.yaml"
        ):
            # Skip hidden files except specific ones we want
            if item.is_dir() and item.name == ".github":
                pass  # Allow .github directory
            else:
                continue
            
        # Handle filename templating
        dest_name = item.name
        if "{{ project_slug }}" in dest_name:
            dest_name = dest_name.replace("{{ project_slug }}", context["project_slug"])
        if "[[ project_slug ]]" in dest_name:
            dest_name = dest_name.replace("[[ project_slug ]]", context["project_slug"])

        current_dest = dest / dest_name

        if item.is_dir():
            current_dest.mkdir(exist_ok=True)
            _copy_template_dir(item, current_dest, env, context)
        else:
            _process_file(item, current_dest, env, context)


def _process_file(source: Path, dest: Path, env: Environment, context: dict):
    """
    Process a single template file.
    """
    # Determine if this file should be rendered
    should_render = (
        source.suffix == ".j2" or
        source.suffix == ".py-tpl" or
        source.name.endswith(".md") or
        source.name in ("Makefile", ".gitignore") or
        source.suffix in (".py", ".js", ".vue", ".json", ".yml", ".yaml", ".conf", ".ini")
    )
    
    # Handle .j2 suffix removal
    dest_name = dest.name
    if dest_name.endswith(".j2"):
        dest_name = dest_name[:-3]
        dest = dest.parent / dest_name
    
    if should_render:
        try:
            # Get relative path for template loader
            rel_path = source.relative_to(env.loader.searchpath[0])
            template = env.get_template(str(rel_path))
            rendered = template.render(**context)
            
            with open(dest, "w", encoding="utf-8") as f:
                f.write(rendered)
        except Exception as e:
            # If rendering fails, just copy the file
            shutil.copy2(source, dest)
    else:
        # Binary or non-template files - just copy
        shutil.copy2(source, dest)
