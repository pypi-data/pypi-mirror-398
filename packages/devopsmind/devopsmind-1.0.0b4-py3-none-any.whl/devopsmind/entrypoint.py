import sys
from rich.console import Console
from .cli import main

console = Console()

def run():
    try:
        main()
    except KeyboardInterrupt:
        console.print("")  # clean exit, no traceback
        sys.exit(0)
