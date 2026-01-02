#!/usr/bin/env python3
"""
Setup uv and Python environment for agentic-dev-boilerplate

This script installs uv and sets up the Python virtual environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout.strip() if capture_output else None
    except Exception as e:
        print(f"Error running command: {e}")
        return False, None

def install_uv():
    """Install uv if not already installed."""
    print("🔧 Checking for uv...")

    # Check if uv is already installed
    success, _ = run_command("uv --version")
    if success:
        print("✅ uv is already installed")
        return True

    print("📦 Installing uv...")

    # Install uv using the official installer
    install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
    success, _ = run_command(install_cmd)

    if success:
        print("✅ uv installed successfully")
        # Add uv to PATH for current session
        uv_path = os.path.expanduser("~/.cargo/bin")
        if uv_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{uv_path}:{os.environ.get('PATH', '')}"
        return True
    else:
        print("❌ Failed to install uv")
        return False

def setup_venv():
    """Set up Python virtual environment with uv."""
    print("🐍 Setting up Python virtual environment...")

    # Create virtual environment
    success, _ = run_command("uv venv")
    if not success:
        print("❌ Failed to create virtual environment")
        return False

    print("✅ Virtual environment created")

    # Install dependencies
    if Path("pyproject.toml").exists():
        print("📦 Installing dependencies from pyproject.toml...")
        success, _ = run_command("uv pip install -e .")
        if success:
            print("✅ Dependencies installed")
            return True
        else:
            print("❌ Failed to install dependencies")
            return False
    else:
        print("⚠️  No pyproject.toml found, skipping dependency installation")
        return True

def main():
    print("🚀 Setting up agentic-dev-boilerplate development environment...")

    # Install uv
    if not install_uv():
        sys.exit(1)

    # Setup virtual environment
    if not setup_venv():
        sys.exit(1)

    print("\n🎉 Setup complete!")
    print("\nTo activate the virtual environment, run:")
    print("  source .venv/bin/activate")
    print("\nTo run commands with uv:")
    print("  uv run python your_script.py")
    print("  uv run pytest")

if __name__ == "__main__":
    main()