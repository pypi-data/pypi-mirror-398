import click
import sys
from pathlib import Path
from .utils import create_project_structure, write_template, get_template_content

@click.command()
@click.argument("project_name")
def main(project_name):
    """Create a new FastAPI project structure."""
    project_path = Path.cwd() / project_name
    
    if project_path.exists():
        click.echo(f"Error: Directory '{project_name}' already exists.")
        sys.exit(1)
    
    click.echo(f"Creating project '{project_name}'...")
    
    try:
        # Create folders
        create_project_structure(project_path)
        
        # Write files from templates
        templates = {
            "main.py": "app/main.py",
            "routes.py": "app/api/routes.py",
            "config.py": "app/core/config.py",
            "test_main.py": "tests/test_main.py",
            "env": ".env",
            "gitignore": ".gitignore",
            "requirements.txt": "requirements.txt",
            "README.md": "README.md",
        }
        
        for tmpl_name, target_rel_path in templates.items():
            content = get_template_content(tmpl_name, project_name=project_name)
            write_template(project_path / target_rel_path, content)
            
        click.echo(f"Successfully created project '{project_name}'!")
        click.echo(f"\nTo get started:")
        click.echo(f"  cd {project_name}")
        click.echo(f"  pip install -r requirements.txt")
        click.echo(f"  fastapi dev app/main.py")
        
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
