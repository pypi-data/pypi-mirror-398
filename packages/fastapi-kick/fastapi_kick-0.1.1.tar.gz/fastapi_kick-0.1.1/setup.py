from setuptools import setup, find_packages
from pathlib import Path

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8") if (this_dir / "README.md").exists() else "FastAPI project scaffolder."

setup(
    name="fastapi_kick",
    version="0.1.1",
    packages=find_packages(),
    py_modules=["cli"],
    package_data={
        "commands": [
            "templates/*",
            "templates/**",
        ]
    },
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "python-dotenv",
        "asyncpg",
        "psycopg2-binary"
    ],
    author="Your Name",
    author_email="you@example.com",
    description="FastAPI app scaffolder with health, modules, and Postgres",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://example.com/fastapi_kick",
    entry_points={
        "console_scripts": [
            "fastapi_kick=cli:main"
        ]
    }
)
