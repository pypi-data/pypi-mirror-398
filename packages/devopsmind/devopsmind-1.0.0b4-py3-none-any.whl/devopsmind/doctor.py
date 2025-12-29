# doctor.py

import platform
import shutil
import sys
from rich.table import Table

from .utils import challenges_exist, data_dir_writable


def run_doctor():
    """
    Perform environment checks and return a Rich renderable.
    """

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Status")

    # Python version
    py_ok = sys.version_info >= (3, 8)
    table.add_row(
        "Python version ≥ 3.8",
        "✅" if py_ok else "❌"
    )

    # OS
    table.add_row(
        "Operating System",
        platform.system()
    )

    # Data dir
    table.add_row(
        "Data directory writable",
        "✅" if data_dir_writable() else "❌"
    )

    # Challenges
    table.add_row(
        "Bundled challenges found",
        "✅" if challenges_exist() else "❌"
    )

    # Git
    table.add_row(
        "git installed",
        "✅" if shutil.which("git") else "❌"
    )

    return table
