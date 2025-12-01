"""Models de dades per a TechShop.

Aquest mòdul conté les classes que representen les entitats de la base de dades
i proporciona funcions d'accés a les dades seguint la capa de models.

Cada classe encapsula la lògica d'accés a la base de dades per a les seves
respectives entitats, separant així la lògica de dades de la lògica de negoci
i de presentació.
"""
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from werkzeug.security import check_password_hash
import time
from collections import defaultdict


# Memòria simple en procés per protegir contra força bruta bàsica
_FAILED_LOGINS = defaultdict(list)  # username -> [timestamps]
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 60


def _register_failed_login(username: str) -> None:
    """Registra un intent fallit d'inici de sessió per a un usuari."""
    now = time.time()
    attempts = _FAILED_LOGINS[username]
    # Eliminar intents fora de la finestra
    _FAILED_LOGINS[username] = [ts for ts in attempts if now - ts <= _WINDOW_SECONDS]
    _FAILED_LOGINS[username].append(now)


def _is_rate_limited(username: str) -> bool:
    """Comprova si un usuari ha superat el límit d'intents en la finestra definida."""
    now = time.time()
    attempts = _FAILED_LOGINS.get(username, [])
    attempts = [ts for ts in attempts if now - ts <= _WINDOW_SECONDS]
    _FAILED_LOGINS[username] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


@dataclass
class Product:
    """Model que representa un producte."""
    id: int
    name: str
    price: float
    stock: int
    
    @staticmethod
    def get_all(db_path: Path) -> List['Product']:
        """Obté tots els productes de la base de dades.
        
        Args:
            db_path: ruta al fitxer de base de dades
            
        Returns:
            Llista de productes
        """
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM Product ORDER BY name")
            rows = cur.fetchall()
            return [Product(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(product_id: int, db_path: Path) -> Optional['Product']:
        """Obté un producte per ID.
        
        Args:
            product_id: identificador del producte
            db_path: ruta al fitxer de base de dades
            
        Returns:
            Producte o None si no existeix
        """
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM Product WHERE id = ?", (product_id,))
            row = cur.fetchone()
            if row:
                return Product(**dict(row))
            return None
    
    def update_stock(self, new_stock: int, db_path: Path) -> bool:
        """Actualitza el stock del producte.
        
        Args:
            new_stock: nou valor de stock
            db_path: ruta al fitxer de base de dades
            
        Returns:
            True si s'ha actualitzat correctament
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute("UPDATE Product SET stock = ? WHERE id = ?", (new_stock, self.id))
                conn.commit()
                return cur.rowcount > 0
        except sqlite3.Error:
            return False


@dataclass
class UserAccount:
    """Model que representa un compte d'usuari."""
    id: int
    username: str
    password_hash: str
    salt: str
    email: str
    created_at: str
    
    @staticmethod
    def create(username: str, password_hash: str, salt: str, email: str, db_path: Path) -> int:
        """Crea un nou compte d'usuari.
        
        Args:
            username: nom d'usuari
            password_hash: hash de la contrasenya (incloent la salt)
            salt: salt única per a aquest usuari
            email: correu electrònic
            db_path: ruta al fitxer de base de dades
            
        Returns:
            ID del nou usuari creat
            
        Raises:
            sqlite3.IntegrityError: si el username o email ja existeixen
        """
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO UserAccount (username, password_hash, salt, email) VALUES (?, ?, ?, ?)",
                (username, password_hash, salt, email)
            )
            conn.commit()
            return cur.lastrowid
    
    @staticmethod
    def get_by_username(username: str, db_path: Path) -> Optional['UserAccount']:
        """Obté un usuari pel nom d'usuari.
        
        Args:
            username: nom d'usuari
            db_path: ruta al fitxer de base de dades
            
        Returns:
            Usuari o None si no existeix
        """
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM UserAccount WHERE username = ?", (username,))
            row = cur.fetchone()
            if row:
                return UserAccount(**dict(row))
            return None
    
    @staticmethod
    def authenticate(username: str, password: str, db_path: Path) -> Optional['UserAccount']:
        """Autentica un usuari amb el nom d'usuari i contrasenya.
        
        Args:
            username: nom d'usuari
            password: contrasenya en text pla
            db_path: ruta al fitxer de base de dades
            
        Returns:
            Usuari autenticat o None si les credencials són incorrectes
        """
        # Protecció bàsica contra força bruta per usuari
        if _is_rate_limited(username):
            return None

        user = UserAccount.get_by_username(username, db_path)
        if user is None:
            return None

        # La contrasenya es deriva combinant una salt forta per usuari + password,
        # posteriorment hashida amb PBKDF2 (vegeu create_order/init_db/tests).
        candidate = f"{user.salt}{password}"

        if check_password_hash(user.password_hash, candidate):
            # Login correcte: netegem intents fallits
            _FAILED_LOGINS.pop(username, None)
            return user

        # Registrem intent fallit
        _register_failed_login(username)
        return None


@dataclass
class Order:
    """Model que representa una comanda."""
    id: int
    total: float
    created_at: str
    user_id: int
    
    @staticmethod
    def create(total: float, user_id: int, db_path: Path) -> int:
        """Crea una nova comanda.
        
        Args:
            total: total de la comanda
            user_id: ID de l'usuari
            db_path: ruta al fitxer de base de dades
            
        Returns:
            ID de la nova comanda creada
        """
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO \"Order\" (total, user_id) VALUES (?, ?)",
                (total, user_id)
            )
            conn.commit()
            return cur.lastrowid


@dataclass
class OrderItem:
    """Model que representa un element d'una comanda."""
    id: int
    order_id: int
    product_id: int
    quantity: int
    
    @staticmethod
    def create(order_id: int, product_id: int, quantity: int, db_path: Path) -> int:
        """Afegeix un element a una comanda.
        
        Args:
            order_id: ID de la comanda
            product_id: ID del producte
            quantity: quantitat
            db_path: ruta al fitxer de base de dades
            
        Returns:
            ID del nou element creat
        """
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO OrderItem (order_id, product_id, quantity) VALUES (?, ?, ?)",
                (order_id, product_id, quantity)
            )
            conn.commit()
            return cur.lastrowid

