"""
Configuració base per a l'aplicació TechShop.

Les subclasses (DevConfig, ProdConfig) especialitzen aquesta configuració
per a cada entorn.
"""
import os
from pathlib import Path


class BaseConfig:
    """Configuració comuna a tots els entorns."""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    # Clau secreta per a sessions, CSRF, etc.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Ruta a la base de dades SQLite per defecte
    DB_PATH = PROJECT_ROOT / "database" / "db.sqlite3"

    # Flags generals
    DEBUG = False
    TESTING = False


class DevConfig(BaseConfig):
    """Configuració per a desenvolupament."""

    DEBUG = True


class ProdConfig(BaseConfig):
    """Configuració per a producció."""

    DEBUG = False

    # En producció exigim SECRET_KEY des de l'entorn
    SECRET_KEY = os.environ.get("SECRET_KEY")



