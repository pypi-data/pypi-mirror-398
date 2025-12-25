import os
from pathlib import Path

def create_project_structure(base_path: Path):
    """Creates the base FastAPI project structure."""
    folders = [
        "app/api",
        "app/core",
        "app/models",
        "app/schemas",
        "app/services",
        "tests",
    ]
    for folder in folders:
        os.makedirs(base_path / folder, exist_ok=True)
        # Create __init__.py in each folder
        (base_path / folder / "__init__.py").touch()
    
    # Also create app/__init__.py
    (base_path / "app" / "__init__.py").touch()

def write_template(file_path: Path, content: str):
    """Writes content to a file, ensuring parent directories exist."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content.strip() + "\n")

def get_template_content(template_name: str, **kwargs) -> str:
    """Returns the content of a template file, optionally formatted."""
    template_path = Path(__file__).parent / "templates" / f"{template_name}.tmpl"
    with open(template_path, "r") as f:
        content = f.read()
    return content.format(**kwargs)
