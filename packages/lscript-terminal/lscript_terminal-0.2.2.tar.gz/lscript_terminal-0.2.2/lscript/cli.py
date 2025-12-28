#!/usr/bin/env python3
"""
Point d'entrée CLI pour LScript.

Usage:
    python -m lscript        # Lance le shell interactif
    python -m lscript --help # Affiche l'aide
"""

import argparse
import sys

from lscript import __version__
from lscript.shell import LScriptShell


def create_parser() -> argparse.ArgumentParser:
    """Crée le parser d'arguments CLI."""
    parser = argparse.ArgumentParser(
        prog="lscript",
        description="Terminal intelligent orienté humain",
        epilog="Plus d'infos: https://lscript.fr",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"LScript {__version__}",
    )
    return parser


def main() -> int:
    """Point d'entrée principal."""
    parser = create_parser()
    parser.parse_args()
    
    shell = LScriptShell()
    return shell.run()


if __name__ == "__main__":
    sys.exit(main())
