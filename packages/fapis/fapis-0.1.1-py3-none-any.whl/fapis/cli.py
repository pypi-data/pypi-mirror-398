# fapis/cli.py
import shutil
from pathlib import Path
import click
import subprocess
from pathlib import Path

def init_git(destination: Path):
    """Initialize a git repository at the destination folder."""
    try:
        subprocess.run(["git", "init"], cwd=destination, check=True)
        subprocess.run(["git", "add", "."], cwd=destination, check=True)
        print(f"Git repository initialized in {destination}")
    except FileNotFoundError:
        print("Git is not installed or not in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")


@click.command()
@click.argument("template")
@click.argument("destination", default=".")
def main(template, destination):
    """Generate a FastAPI starter project."""
    script_dir = Path(__file__).parent
    templates_dir = script_dir / "templates" / "infrastructure"

    if template == "base":
        base_folder = templates_dir / "base"
        destination_folder = Path(destination).resolve()
        try:
            shutil.copytree(base_folder, destination_folder)
            click.echo(f"FastAPI base project created at: {destination_folder}")
            init_git(destination_folder)
        except FileExistsError:
            click.echo(f"Error: Destination '{destination_folder}' already exists.")
        except Exception as e:
            click.echo(f"Unexpected error occurred: {e}")
    else:
        click.echo(f"Unknown template: {template}")
