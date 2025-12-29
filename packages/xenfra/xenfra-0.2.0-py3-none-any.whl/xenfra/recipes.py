from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def generate_stack(context: dict):
    """
    Generates a cloud-init startup script from a Jinja2 template.
    
    Args:
        context: A dictionary containing information for rendering the template,
                 e.g., {'domain': 'example.com', 'email': 'user@example.com'}
    """
    # Path to the templates directory
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))

    template = env.get_template("cloud-init.sh.j2")
    
    # The non-dockerized logic has been removed as we are focusing on
    # a purely Docker-based deployment strategy for simplicity and scalability.
    # The context will contain all necessary variables for the template.
    script = template.render(context)
    
    return script
