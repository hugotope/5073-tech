"""Repositori base amb gestió de connexió a la base de dades.

Aquest mòdul proporciona una classe base per a repositoris que centralitza
la gestió de connexió a la base de dades i proporciona mètodes útils comuns.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Iterator


class BaseRepository:
    """Classe base per a repositoris amb gestió de connexió centralitzada."""
    
    def __init__(self, db_path: Path):
        """Inicialitza el repositori amb la ruta a la base de dades.
        
        Args:
            db_path: ruta al fitxer de base de dades SQLite
        """
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self, row_factory: Optional[type] = sqlite3.Row) -> Iterator[sqlite3.Connection]:
        """Context manager per obtenir una connexió a la base de dades.
        
        Garanteix que la connexió es tanca correctament després de l'ús.
        Activa les claus foranes per defecte.
        
        Args:
            row_factory: factory per a les files (per defecte sqlite3.Row)
            
        Yields:
            Connexió SQLite configurada
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('PRAGMA foreign_keys = ON;')
            if row_factory:
                conn.row_factory = row_factory
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def transaction(self, row_factory: Optional[type] = sqlite3.Row) -> Iterator[sqlite3.Connection]:
        """Context manager per a una transacció de base de dades.
        
        Garanteix commit automàtic si tot va bé, o rollback en cas d'error.
        
        Args:
            row_factory: factory per a les files (per defecte sqlite3.Row)
            
        Yields:
            Connexió SQLite dins d'una transacció
            
        Example:
            with repo.transaction() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO ...")
                # Commit automàtic al sortir del context
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('PRAGMA foreign_keys = ON;')
            if row_factory:
                conn.row_factory = row_factory
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

