import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

def start_project(project_name: str):
    target_dir = Path.cwd() / project_name

    if target_dir.exists():
        print("❌ Directory already exists")
        return

    shutil.copytree(TEMPLATE_DIR, target_dir)

    # Replace placeholders
    for file in target_dir.rglob("*.py"):
        content = file.read_text()
        content = content.replace("{{project_name}}", project_name)
        file.write_text(content)

    print(f"✅ FastAPI project '{project_name}' created successfully")
