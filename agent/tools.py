# agent/tools.py
import subprocess
from pathlib import Path
from langchain.tools import tool

# ─── Workspace (sandbox) ────────────────────────────────────────────────────
# resolve() convierte a ruta absoluta — importante para que las comparaciones funcionen
WORKSPACE = Path("workspace").resolve()

def safe_path(relative_path: str) -> Path:
    """
    Convierte una ruta relativa a absoluta dentro del workspace.
    Lanza un error si el agente intenta salir del sandbox.
    
    Equivalente TS:
      const safePath = path.resolve('./workspace', relativePath)
      if (!safePath.startsWith(WORKSPACE)) throw new Error(...)
    """
    # Construimos la ruta completa
    full_path = (WORKSPACE / relative_path).resolve()

    # is_relative_to() verifica que full_path esté DENTRO de WORKSPACE
    # Esto previene ataques de path traversal como "../../etc/passwd"
    if not full_path.is_relative_to(WORKSPACE):
        raise ValueError(f"Ruta no permitida: '{relative_path}' está fuera del workspace.")

    return full_path


# ─── Tools ──────────────────────────────────────────────────────────────────

@tool
def read_file(path: str) -> str:
    """
    Reads the content of a file inside the workspace.
    Use this to understand existing code before modifying it.

    Args:
        path: Relative path to the file inside the workspace (e.g. 'main.py' or 'src/utils.py')
    """
    try:
        file_path = safe_path(path)

        if not file_path.exists():
            return f"Error: el archivo '{path}' no existe."

        if not file_path.is_file():
            return f"Error: '{path}' no es un archivo."

        return file_path.read_text(encoding="utf-8")

    except ValueError as e:
        return f"Error de seguridad: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """
    Creates or overwrites a file inside the workspace with the given content.
    Use this to create new files or update existing ones.

    Args:
        path: Relative path to the file inside the workspace (e.g. 'main.py')
        content: The full content to write to the file
    """
    try:
        file_path = safe_path(path)

        # mkdir(parents=True) crea carpetas intermedias si no existen
        # exist_ok=True no lanza error si ya existe — como mkdir -p
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return f"Archivo '{path}' guardado exitosamente."

    except ValueError as e:
        return f"Error de seguridad: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """
    Lists all files and folders inside a directory in the workspace.
    Use this to understand the structure of the project before reading or modifying files.

    Args:
        path: Relative path to the directory inside the workspace. Defaults to root workspace.
    """
    try:
        dir_path = safe_path(path)

        if not dir_path.exists():
            return f"Error: el directorio '{path}' no existe."

        if not dir_path.is_dir():
            return f"Error: '{path}' no es un directorio."

        items = []
        for item in sorted(dir_path.iterdir()):
            # Mostramos si es archivo o carpeta con un prefijo visual
            prefix = "📁" if item.is_dir() else "📄"
            items.append(f"{prefix} {item.name}")

        if not items:
            return f"El directorio '{path}' está vacío."

        return "\n".join(items)

    except ValueError as e:
        return f"Error de seguridad: {e}"


@tool
def run_python(path: str) -> str:
    """
    Executes a Python file inside the workspace and returns its output.
    Use this to verify that code works correctly after writing or modifying it.

    Args:
        path: Relative path to the .py file to execute (e.g. 'main.py')
    """
    try:
        file_path = safe_path(path)

        if not file_path.exists():
            return f"Error: el archivo '{path}' no existe."

        if file_path.suffix != ".py":
            return f"Error: '{path}' no es un archivo Python (.py)."

        # subprocess.run ejecuta un comando del sistema y captura el output
        # Equivalente a child_process.execSync en Node.js
        result = subprocess.run(
            ["python", str(file_path)],
            capture_output=True,   # captura stdout y stderr
            text=True,             # retorna strings en vez de bytes
            timeout=15,            # mata el proceso si tarda más de 15 segundos
            cwd=WORKSPACE          # ejecuta desde el workspace como directorio raíz
        )

        output = result.stdout
        errors = result.stderr

        if errors:
            return f"Output:\n{output}\n\nErrors:\n{errors}" if output else f"Error:\n{errors}"

        return output if output else "El script se ejecutó sin output."

    except subprocess.TimeoutExpired:
        return "Error: el script tardó más de 15 segundos y fue cancelado."
    except ValueError as e:
        return f"Error de seguridad: {e}"


# ─── Exportamos ──────────────────────────────────────────────────────────────
tools = [read_file, write_file, list_directory, run_python]
tools_by_name = {tool.name: tool for tool in tools}
