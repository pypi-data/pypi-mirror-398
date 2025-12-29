import os
import tomllib  # Python 3.11+

def get_project_context():
    """
    Scans for project configuration.
    Prioritizes: pyproject.toml > requirements.txt
    Prioritizes: uv > poetry > pip
    """
    options = {}
    
    # 1. Check for Lockfiles (Determines the Manager)
    if os.path.exists("uv.lock"):
        options["uv"] = True
    if os.path.exists("poetry.lock"):
        options["poetry"] = True
    
    # 2. Extract Dependencies from pyproject.toml (Best source for names)
    if os.path.exists("pyproject.toml"):
        try:
            with open("pyproject.toml", "rb") as f:
                data = tomllib.load(f)
                deps = data.get("project", {}).get("dependencies", [])
                if deps:
                    # Clean versions if needed, or just pass them to pip/uv
                    options["toml"] = " ".join(deps)
        except Exception:
            pass

    # 3. Extract Dependencies from requirements.txt (Fallback source)
    if os.path.exists("requirements.txt"):
        try:
            with open("requirements.txt", "r") as f:
                pkgs = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                if pkgs:
                    options["pip"] = " ".join(pkgs)
        except:
            pass

    # --- DECISION LOGIC ---
    context = {"type": "pip", "packages": None, "conflict": False}
    
    # A. Determine the Manager (Type)
    if "uv" in options:
        context["type"] = "uv"
    elif "poetry" in options:
        context["type"] = "poetry"
    else:
        context["type"] = "pip"

    # B. Determine the Packages (Content)
    # We prefer TOML because it's the modern standard usually paired with UV/Poetry
    if "toml" in options:
        context["packages"] = options["toml"]
    elif "pip" in options:
        context["packages"] = options["pip"]

    # C. Check for "True" Conflicts
    # A conflict is when we have ambiguous package sources (TOML vs Requirements)
    # AND we aren't sure which one the user wants.
    if "toml" in options and "pip" in options:
        # If we have both, we flag it so the UI can ask (or default to TOML)
        context["conflict"] = True
        context["choices"] = {
            "1": {"name": "pyproject.toml", "pkgs": options["toml"]},
            "2": {"name": "requirements.txt", "pkgs": options["pip"]}
        }

    return context