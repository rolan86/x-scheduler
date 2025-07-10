#!/usr/bin/env python
"""Quick test script to verify CLI functionality."""

import subprocess
import sys


def run_command(cmd: str) -> None:
    """Run a CLI command and print the output."""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
            
        if result.returncode != 0:
            print(f"Command failed with return code: {result.returncode}")
    except Exception as e:
        print(f"Error running command: {e}")


def main():
    """Test various CLI commands."""
    commands = [
        "python -m src.cli.main --version",
        "python -m src.cli.main --help",
        "python -m src.cli.main generate --help",
        "python -m src.cli.main init",
        "python -m src.cli.main queue list",
        "python -m src.cli.main stats --period week",
    ]
    
    print("Testing X-Scheduler CLI...")
    
    for cmd in commands:
        run_command(cmd)
    
    print("\n" + "="*60)
    print("CLI test complete!")
    print("="*60)


if __name__ == "__main__":
    main()