"""
TAI-API Main File Generator

Este módulo genera el archivo __main__.py principal de la aplicación FastAPI
basándose en el estado actual del proyecto y las funcionalidades disponibles.
"""

from .main import MainFileGenerator

__all__ = [
    "MainFileGenerator",
    "generate_main_file", 
    "get_project_status"
]
