"""
Installation verification script.
Run this to check if everything is set up correctly.
"""

import sys
import os
from pathlib import Path

# Fix Unicode output on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def check_dependencies():
    """Check required packages."""
    print("\nChecking dependencies...")
    required = [
        "streamlit",
        "httpx",
        "yaml",
        "dotenv",
        "pandas"
    ]

    all_ok = True
    for package in required:
        try:
            if package == "yaml":
                __import__("yaml")
            elif package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} not found")
            all_ok = False

    return all_ok

def check_project_structure():
    """Check project directory structure."""
    print("\nChecking project structure...")

    required_dirs = [
        "config",
        "core",
        "api",
        "prompts",
        "ui",
        "utils",
        "tests",
        "outputs"
    ]

    all_ok = True
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✓ {dir_name}/ directory exists")
        else:
            print(f"✗ {dir_name}/ directory missing")
            all_ok = False

    return all_ok

def check_config_files():
    """Check configuration files."""
    print("\nChecking configuration files...")

    required_files = [
        "config/models.yaml",
        "config/user_profile.yaml",
        "config/settings.py",
        ".env.example",
        "requirements.txt",
        "app.py"
    ]

    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_ok = False

    return all_ok

def check_env_file():
    """Check .env file."""
    print("\nChecking .env file...")

    if Path(".env").exists():
        print("✓ .env file exists")

        # Try to read API key
        try:
            from dotenv import load_dotenv
            load_dotenv()

            api_key = os.getenv("OPENROUTER_API_KEY", "")

            if api_key and api_key != "your_key_here":
                print("✓ API key configured")
                return True
            else:
                print("⚠ .env exists but API key not set")
                print("  Edit .env and add your OpenRouter API key")
                return False

        except Exception as e:
            print(f"⚠ Error reading .env: {e}")
            return False
    else:
        print("⚠ .env file not found")
        print("  Copy .env.example to .env and add your API key")
        return False

def check_imports():
    """Check if core modules can be imported."""
    print("\nChecking module imports...")

    modules = [
        "config.settings",
        "api.openrouter_client",
        "core.council",
        "utils.validator"
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} imports successfully")
        except Exception as e:
            print(f"✗ {module} import failed: {e}")
            all_ok = False

    return all_ok

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("LLM Council Installation Verification")
    print("=" * 60)

    results = []

    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Project Structure", check_project_structure()))
    results.append(("Config Files", check_config_files()))
    results.append(("Environment File", check_env_file()))
    results.append(("Module Imports", check_imports()))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All checks passed! You're ready to run the application.")
        print("\nTo start the app, run:")
        print("  streamlit run app.py")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Create .env file: cp .env.example .env")
        print("  - Add API key to .env file")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
