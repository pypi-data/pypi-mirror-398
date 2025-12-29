import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def detect_framework(path="."):
    """
    Scans common Python project structures to guess the framework and entrypoint.
    Returns: (framework_name, default_port, start_command) or (None, None, None)
    """
    project_root = Path(path).resolve()

    # Check for Django first (common pattern: manage.py in root)
    if (project_root / "manage.py").is_file():
        project_name = project_root.name
        return "django", 8000, f"gunicorn {project_name}.wsgi:application --bind 0.0.0.0:8000"

    candidate_files = []
    
    # Check directly in project root
    for name in ["main.py", "app.py"]:
        if (project_root / name).is_file():
            candidate_files.append(project_root / name)

    # Check in src/*/ (standard package layout)
    for src_dir in project_root.glob("src/*"):
        if src_dir.is_dir():
            for name in ["main.py", "app.py"]:
                if (src_dir / name).is_file():
                    candidate_files.append(src_dir / name)

    for file_path in candidate_files:
        with open(file_path, "r") as f:
            content = f.read()
            
            module_name = str(file_path.relative_to(project_root)).replace(os.sep, '.')[:-3]
            if module_name.startswith("src."):
                module_name = module_name[4:]


            if "FastAPI" in content:
                return "fastapi", 8000, f"uvicorn {module_name}:app --host 0.0.0.0 --port 8000"
            
            if "Flask" in content:
                return "flask", 5000, f"gunicorn {module_name}:app -b 0.0.0.0:5000"
    
    return None, None, None

def generate_templated_assets(context: dict):
    """
    Generates deployment assets (Dockerfile, docker-compose.yml) using Jinja2 templates.
    
    Args:
        context: A dictionary containing information for rendering templates,
                 e.g., {'database': 'postgres', 'python_version': 'python:3.11-slim'}
    """
    # Path to the templates directory
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))

    # Detect framework specifics
    framework, port, command = detect_framework()
    if not framework:
        print("Warning: No recognizable web framework detected.")
        return []

    # Merge detected context with provided context
    render_context = {
        'port': port,
        'command': command,
        **context
    }
    
    generated_files = []

    # --- 1. Dockerfile ---
    dockerfile_template = env.get_template("Dockerfile.j2")
    dockerfile_content = dockerfile_template.render(render_context)
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    generated_files.append("Dockerfile")

    # --- 2. docker-compose.yml ---
    compose_template = env.get_template("docker-compose.yml.j2")
    compose_content = compose_template.render(render_context)
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    generated_files.append("docker-compose.yml")

    return generated_files