import os
import shutil
from pathlib import Path
from fastapi_starter.utils import create_project_structure, write_template

def test_create_project_structure(tmp_path):
    project_path = tmp_path / "test_app"
    create_project_structure(project_path)
    
    expected_folders = [
        "app/api",
        "app/core",
        "app/models",
        "app/schemas",
        "app/services",
        "tests",
    ]
    
    for folder in expected_folders:
        assert (project_path / folder).is_dir()
        assert (project_path / folder / "__init__.py").exists()
    
    assert (project_path / "app" / "__init__.py").exists()

def test_write_template(tmp_path):
    file_path = tmp_path / "subdir" / "test.txt"
    content = "test content"
    write_template(file_path, content)
    
    assert file_path.exists()
    with open(file_path, "r") as f:
        assert f.read() == "test content\n"
