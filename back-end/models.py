"""Models de dades per a TechShop.

Aquest mòdul conté les classes que representen les entitats de la base de dades
i proporciona funcions d'accés a les dades seguint la capa de models.

Cada classe encapsula la lògica d'accés a la base de dades per a les seves
respectives entitats, separant així la lògica de dades de la lògica de negoci
i de presentació.
"""
import sqlite3
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pathlib import Path


@dataclass
class Category:
    """Model que representa una categoria de productes."""
    id: int
    name: str
    slug: str

    @staticmethod
    def get_all(db_path: Path) -> List['Category']:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM Category ORDER BY name")
            rows = cur.fetchall()
            return [Category(**dict(row)) for row in rows]

    @staticmethod
    def get_by_id(category_id: int, db_path: Path) -> Optional['Category']:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM Category WHERE id = ?", (category_id,))
            row = cur.fetchone()
            if row:
                return Category(**dict(row))
            return None


@dataclass
class Product:
    """Model que representa un producte."""
    id: int
    name: str
    price: float
    stock: int
    category_id: int = 1
    subcategory_id: Optional[int] = None

    @staticmethod
    def get_all(
        db_path: Path,
        category_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List['Product']:
        """Obté tots els productes, opcionalment filtrats per categoria i/o nom."""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            sql = "SELECT * FROM Product WHERE 1=1"
            params = []
            if category_id:
                sql += " AND category_id = ?"
                params.append(category_id)
            if search_query and search_query.strip():
                sql += " AND name LIKE ?"
                params.append(f"%{search_query.strip()}%")
            sql += " ORDER BY name"
            cur.execute(sql, params)
            rows = cur.fetchall()
            out = []
            for row in rows:
                d = dict(row)
                d.setdefault("category_id", 1)
                out.append(Product(**d))
            return out
    
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
                d = dict(row)
                d.setdefault("category_id", 1)
                return Product(**d)
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
    email: str
    created_at: str
    segment: Optional[str] = None
    
    @staticmethod
    def create(username: str, password_hash: str, email: str, db_path: Path) -> int:
        """Crea un nou compte d'usuari.
        
        Args:
            username: nom d'usuari
            password_hash: hash de la contrasenya
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
                "INSERT INTO UserAccount (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
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
                d = dict(row)
                d.setdefault("segment")
                return UserAccount(**d)
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
        user = UserAccount.get_by_username(username, db_path)
        if user is None:
            return None
        
        # Generar hash de la contrasenya proporcionada
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Comparar amb el hash emmagatzemat
        if password_hash == user.password_hash:
            return user
        
        return None


@dataclass
class Order:
    """Model que representa una comanda."""
    id: int
    total: float
    created_at: str
    user_id: int
    shipping_city: Optional[str] = None
    shipping_province: Optional[str] = None
    shipping_country: Optional[str] = None

    @staticmethod
    def create(
        total: float,
        user_id: int,
        db_path: Path,
        shipping_city: Optional[str] = None,
        shipping_province: Optional[str] = None,
        shipping_country: Optional[str] = None,
    ) -> int:
        """Crea una nova comanda.

        Args:
            total: total de la comanda
            user_id: ID de l'usuari
            db_path: ruta al fitxer de base de dades
            shipping_city: ciutat d'enviament (per anàlisi geogràfica)
            shipping_province: província
            shipping_country: país

        Returns:
            ID de la nova comanda creada
        """
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO "Order" (total, user_id, shipping_city, shipping_province, shipping_country)
                   VALUES (?, ?, ?, ?, ?)""",
                (total, user_id, shipping_city, shipping_province, shipping_country),
            )
            conn.commit()
            return cur.lastrowid
    
    @staticmethod
    def get_by_id(order_id: int, db_path: Path) -> Optional['Order']:
        """Obté una comanda per ID.
        
        Args:
            order_id: identificador de la comanda
            db_path: ruta al fitxer de base de dades
            
        Returns:
            Comanda o None si no existeix
        """
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM \"Order\" WHERE id = ?", (order_id,))
            row = cur.fetchone()
            if row:
                d = dict(row)
                d.setdefault("shipping_city")
                d.setdefault("shipping_province")
                d.setdefault("shipping_country")
                return Order(**d)
            return None


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
    
    @staticmethod
    def get_by_order_id(order_id: int, db_path: Path) -> List['OrderItem']:
        """Obté tots els elements d'una comanda.
        
        Args:
            order_id: ID de la comanda
            db_path: ruta al fitxer de base de dades
            
        Returns:
            Llista d'elements de la comanda
        """
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM OrderItem WHERE order_id = ?", (order_id,))
            rows = cur.fetchall()
            return [OrderItem(**dict(row)) for row in rows]

