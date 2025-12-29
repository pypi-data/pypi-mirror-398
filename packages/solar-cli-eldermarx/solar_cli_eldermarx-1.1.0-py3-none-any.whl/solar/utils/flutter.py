"""
SOLAR CLI - Flutter Utilities
"""

import subprocess
import shutil

def check_flutter_installed() -> bool:
    """Check if Flutter is installed and accessible in the system PATH"""
    # Check if flutter command exists
    if shutil.which('flutter') is None:
        return False
    
    try:
        # Try to run flutter --version to ensure it's working
        result = subprocess.run(
            ['flutter', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def add_flutter_packages(project_path: str, packages: list):
    """Add Flutter packages to the project"""
    if not packages:
        return
    
    import subprocess
    from rich.console import Console
    console = Console()
    
    for package in packages:
        try:
            console.print(f"  [cyan]• Adding package: [bold]{package}[/bold][/cyan]")
            subprocess.run(
                ['flutter', 'pub', 'add', package],
                cwd=project_path,
                capture_output=True,
                check=True
            )
        except Exception as e:
            console.print(f"  [red]⚠ Failed to add package {package}: {e}[/red]")
