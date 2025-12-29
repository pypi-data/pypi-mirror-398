import sys
from commands.start import start_project

def main():
    if len(sys.argv) < 3:
        print("Usage: fastapi_kick start <project_name>")
        sys.exit(1)

    command = sys.argv[1]
    project_name = sys.argv[2]

    if command == "start":
        start_project(project_name)
    else:
        print("Unknown command")
