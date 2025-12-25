import os
import sys
import subprocess
import platform

PROJECT_NAME = "my_project"

FILES = {
    "src/my_project/__init__.py": '__version__ = "0.1.0"\n',

    "src/my_project/main.py": (
        "def main():\n"
        "    print(\"Hello, world\")\n\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    ),

    "src/my_project/__main__.py": (
        "from .main import main\n\n"
        "main()\n"
    ),

    "tests/test_main.py": (
        "def test_true():\n"
        "    assert True\n"
    ),

    ".gitignore": (
        "__pycache__/\n"
        "*.pyc\n"
        ".env\n"
        ".venv/\n"
        "dist/\n"
        "build/\n"
    ),

    ".dockerignore": (
        "__pycache__/\n"
        "*.pyc\n"
        ".env\n"
        ".venv/\n"
        "tests/\n"
        ".git/\n"
    ),

    ".gitattributes": (
        "* text=auto\n"
        "*.py text diff=python\n"
        "*.md text\n"
    ),

    "README.md": (
        "# My Project\n\n"
        "Minimal but production-ready Python project.\n\n"
        "## Setup\n"
        "source .venv/bin/activate  # macOS/Linux\n"
        ".venv\\Scripts\\activate   # Windows\n\n"
        "## Run\n"
        "python -m my_project\n"
    ),

    "requirements.txt": "requests\n",

    "pyproject.toml": (
        "[project]\n"
        "name = \"my_project\"\n"
        "version = \"0.1.0\"\n"
        "requires-python = \">=3.10\"\n"
        "dependencies = [\"requests\"]\n"
    ),

    "Dockerfile": (
        "FROM python:3.12-slim\n\n"
        "WORKDIR /app\n"
        "COPY requirements.txt .\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n"
        "COPY src/ src/\n"
        "CMD [\"python\", \"-m\", \"my_project\"]\n"
    ),

    "LICENSE": (
        "MIT License\n"
        "\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files (the \"Software\"), to deal\n"
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n"
        "\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n"
        "\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n"

    ),
}


def create_files_in_current_dir():
    for path, content in FILES.items():
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def create_venv():
    python_exec = sys.executable
    subprocess.run(
        [python_exec, "-m", "venv", ".venv"],
        check=True
    )


def attempt_activation():
    system = platform.system().lower()

    if system == "windows":
        activate_cmd = ".venv\\Scripts\\activate"
        shell = True
    else:
        activate_cmd = "source .venv/bin/activate"
        shell = True

    print("\nVirtual environment created.")
    print("To activate it, run:\n")
    print(activate_cmd)
    print()


def main():
    print("Creating project files...")
    create_files_in_current_dir()

    print("Creating virtual environment...")
    create_venv()

    attempt_activation()

    print("Setup complete ✔")


if __name__ == "__main__":
    main()
