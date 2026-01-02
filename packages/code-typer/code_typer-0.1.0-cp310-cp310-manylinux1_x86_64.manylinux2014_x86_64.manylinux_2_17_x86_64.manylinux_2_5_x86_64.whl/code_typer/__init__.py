"""
code-typer: Terminal-based code showcase tool that simulates human-like typing.

A tool for conference demos, code walkthroughs, and recording programming tutorials.
Replicates the experience of watching someone type code in vim or similar editors.
"""

__version__ = "0.1.0"
__author__ = "Farshid Ashouri"

from code_typer.file_handler import FileHandler
from code_typer.human_behavior import HumanBehavior
from code_typer.typer_engine import TyperEngine

__all__ = ["TyperEngine", "HumanBehavior", "FileHandler", "__version__"]
