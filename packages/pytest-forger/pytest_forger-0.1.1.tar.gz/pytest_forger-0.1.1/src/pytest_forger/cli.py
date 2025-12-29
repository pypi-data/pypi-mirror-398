# ---------------------------------------------------
# Project: pytest_forger (ptf)
# Author: Daryll Lorenzo Alfonso
# Year: 2025
# License: MIT License
# ---------------------------------------------------

"""
Entry point for pytest_forger CLI (`ptf`).

Available commands:
- `ptf version`: Show version and information about pytest-forger
- `ptf forge <source_file.py>`: Forge PyTest tests from existing Python source code
"""

import typer
import sys
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="ptf",
    help="pytest-forger: Forge PyTest-ready tests from existing Python source code.",
    add_completion=False,
    no_args_is_help=True,
)

def get_version() -> str:
    """
    Retrieve the current version of pytest-forger.
    
    Returns:
        str: Version string (e.g., "0.1.0")
    """
    try:
        from pytest_forger import __version__
        return __version__
    except ImportError:
        return "0.1.0-dev"

@app.command()
def version():
    """
    Display version information about pytest-forger.
    
    Shows:
        - Current version number
        - Project repository URL
        - Author and license information
        
    Example:
        $ ptf version
        pytest-forger v0.1.0
        https://github.com/daryll/pytest-forger
        MIT License © 2025 Daryll Lorenzo Alfonso
    """
    version_str = get_version()
    typer.echo(f"pytest-forger v{version_str}")
    typer.echo("https://github.com/daryll/pytest-forger")
    typer.echo("MIT License © 2025 Daryll Lorenzo Alfonso")

@app.command()
def forge(
    source_file: str = typer.Argument(
        ...,
        help="Path to the Python source file to analyze and generate tests for"
    ),
    function_name: Optional[str] = typer.Option(
        None, 
        "--function", "-f",
        help="Generate tests only for a specific function (default: all functions in the module)"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Directory where generated tests will be saved (default: 'tests/' in current directory)"
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite", "-w",
        help="Overwrite existing test files if they already exist"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed information about the test generation process"
    ),
):
    """
    Forge PyTest tests from an existing Python source file.
    
    This command analyzes a Python source file, extracts its functions and classes,
    and generates corresponding PyTest test cases. It creates a test file in the
    'tests' directory (or specified output directory) with appropriate test
    functions for the analyzed code.
    
    Args:
        source_file: Path to the .py file to analyze
        function_name: Optional specific function to target
        output_dir: Optional custom directory for output
        overwrite: Whether to overwrite existing files
        verbose: Enable detailed output
    
    Workflow:
        1. Validates the source file exists and is readable
        2. Analyzes the Python code to extract functions/classes
        3. Creates/verifies the output directory structure
        4. Generates appropriate PyTest test cases
        5. Saves the test file with proper imports and structure
    
    Examples:
        $ ptf forge my_module.py
        $ ptf forge utils/calculator.py --function add --output tests/unit
        $ ptf forge app/models.py --overwrite --verbose
    """
    if verbose:
        typer.echo("🔧 Verbose mode enabled")
        typer.echo(f"Python interpreter: {sys.executable}")
        typer.echo(f"Working directory: {Path('.').absolute()}")
    
    typer.echo(f"🔍 Analyzing source file: {source_file}")
    
    # TODO: Implement the actual forge functionality
    # 1. Validate source file exists and is a Python file
    # 2. Parse the Python file to extract functions/classes
    # 3. Generate appropriate test structure
    # 4. Create tests directory if it doesn't exist
    # 5. Write generated test file
    
    # Placeholder implementation
    typer.echo("📝 Test generation functionality coming soon!")
    typer.echo(f"Target: {source_file}")
    if function_name:
        typer.echo(f"Focusing on function: {function_name}")
    typer.echo(f"Output directory: {output_dir or 'tests/'}")

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Enable verbose output for debugging"
    )
):
    """
    pytest-forger: Automated PyTest test generation.
    
    A CLI tool that analyzes Python source code and generates
    corresponding PyTest test cases to accelerate test writing.
    
    Use 'ptf --help' to see all available commands.
    """
    # Store verbose flag in context for use in commands
    ctx.obj = {"verbose": verbose}

if __name__ == "__main__":
    app()