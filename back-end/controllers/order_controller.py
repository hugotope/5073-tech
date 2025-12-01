"""Controlador per a la gestió de comandes.

Aquest mòdul conté la lògica de negoci relacionada amb les comandes,
incloent la funció create_order que processa una compra.

La funció create_order:
- Calcula el total de la comanda
- Crea o obté l'usuari
- Crea la comanda
- Crea els elements de la comanda (OrderItems)
- Actualitza l'inventari (stock) dels productes de forma atòmica dins d'una
  única transacció de base de dades.
"""
from typing import Dict
from pathlib import Path
import sqlite3
import secrets

from werkzeug.security import generate_password_hash

from models import Product, UserAccount, Order, OrderItem


def calculate_order_total(cart: Dict[str, int], db_path: Path) -> float:
    """Calcula el total d'una comanda basant-se en el carretó.
    
    Args:
        cart: diccionari amb product_id -> quantity
        db_path: ruta a la base de dades
        
    Returns:
        Total de la comanda
    """
    total = 0.0
    
    for product_id, quantity in cart.items():
        product = Product.get_by_id(int(product_id), db_path)
        if product:
            total += product.price * quantity
    
    return total


def create_order(cart: Dict[str, int], username: str, password: str,
                 email: str, db_path: Path) -> int:
    """Crea una comanda i actualitza l'inventari.
    
    Aquesta funció encapçala tota la lògica de creació d'una comanda:
    1. Comprova que hi ha productes al carretó
    2. Valida el stock disponible per a cada producte
    3. Calcula el total de la comanda
    4. Crea o obté l'usuari
    5. Crea la comanda
    6. Crea els elements de la comanda (OrderItems)
    7. Actualitza l'inventari dels productes
    
    Args:
        cart: diccionari amb product_id -> quantity
        username: nom d'usuari
        password: contrasenya (serà hashida)
        email: correu electrònic
        db_path: ruta a la base de dades
        
    Returns:
        ID de la comanda creada
        
    Raises:
        ValueError: si el carretó està buit o si no hi ha stock suficient
        Exception: si hi ha un error al crear la comanda
    """
    if not cart:
        raise ValueError("El carretó està buit")
    
    with sqlite3.connect(db_path) as conn:
        """
        Utilitzem una única connexió/transaction per garantir la consistència:
        - Validació d'estoc
        - Creació (o obtenció) de l'usuari
        - Creació de la comanda i les seves línies
        - Actualització atòmica de l'estoc dels productes
        """
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 1) Valida el stock i calcula el total en aquesta mateixa connexió
            total = 0.0
            for product_id, quantity in cart.items():
                cur.execute(
                    "SELECT id, name, price, stock FROM Product WHERE id = ?",
                    (int(product_id),)
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Producte amb ID {product_id} no trobat")

                if row["stock"] < quantity:
                    raise ValueError(
                        f"Stock insuficient per a {row['name']}: "
                        f"se sol·liciten {quantity} però només hi ha {row['stock']}"
                    )

                total += row["price"] * quantity

            # 2) Crea o obté l'usuari dins de la mateixa transacció
            cur.execute(
                "SELECT * FROM UserAccount WHERE username = ?",
                (username,)
            )
            user_row = cur.fetchone()

            if user_row is None:
                # Crear nou usuari amb salt única per usuari + hash segur de contrasenya
                salt = secrets.token_hex(16)
                password_input = f"{salt}{password}"
                password_hash = generate_password_hash(
                    password_input, method="pbkdf2:sha256", salt_length=16
                )
                cur.execute(
                    "INSERT INTO UserAccount (username, password_hash, salt, email) "
                    "VALUES (?, ?, ?, ?)",
                    (username, password_hash, salt, email)
                )
                user_id = cur.lastrowid
            else:
                user_id = user_row["id"]

            # 3) Crea la comanda
            cur.execute(
                'INSERT INTO "Order" (total, user_id) VALUES (?, ?)',
                (total, user_id)
            )
            order_id = cur.lastrowid

            # 4) Crea els elements de la comanda i actualitza l'inventari de forma atòmica
            for product_id, quantity in cart.items():
                # Crea OrderItem
                cur.execute(
                    "INSERT INTO OrderItem (order_id, product_id, quantity) "
                    "VALUES (?, ?, ?)",
                    (order_id, int(product_id), quantity)
                )

                # Actualitza el stock amb condició stock >= quantity per evitar condicions de carrera
                cur.execute(
                    "UPDATE Product "
                    "SET stock = stock - ? "
                    "WHERE id = ? AND stock >= ?",
                    (quantity, int(product_id), quantity)
                )

                if cur.rowcount == 0:
                    # Si no s'ha actualitzat cap fila, l'estoc ha canviat o és insuficient
                    raise ValueError(
                        f"Stock insuficient o inconsistent per al producte ID {product_id}"
                    )

            conn.commit()
            return order_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al crear la comanda: {str(e)}")

