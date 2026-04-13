"""Controlador per a la gestió de comandes.

Aquest mòdul conté la lògica de negoci relacionada amb les comandes,
incloent la funció create_order que processa una compra.

La funció create_order:
- Calcula el total de la comanda
- Crea o obté l'usuari
- Crea la comanda
- Crea els elements de la comanda (OrderItems)
- Actualitza l'inventari (stock) dels productes
"""
import hashlib
from typing import Dict
from pathlib import Path
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


def create_order(
    cart: Dict[str, int],
    db_path: Path,
    user_id: int = None,
    username: str = None,
    password: str = None,
    email: str = None,
    shipping_city: str = None,
    shipping_province: str = None,
    shipping_country: str = None,
) -> int:
    """Crea una comanda i actualitza l'inventari.
    
    Aquesta funció encapçala tota la lògica de creació d'una comanda:
    1. Comprova que hi ha productes al carretó
    2. Valida el stock disponible per a cada producte
    3. Calcula el total de la comanda
    4. Crea o obté l'usuari (si no s'ha proporcionat user_id)
    5. Crea la comanda
    6. Crea els elements de la comanda (OrderItems)
    7. Actualitza l'inventari dels productes
    
    Args:
        cart: diccionari amb product_id -> quantity
        db_path: ruta a la base de dades
        user_id: ID de l'usuari autenticat (opcional)
        username: nom d'usuari (necessari si no hi ha user_id)
        password: contrasenya (necessària si no hi ha user_id)
        email: correu electrònic (necessari si no hi ha user_id)
        
    Returns:
        ID de la comanda creada
        
    Raises:
        ValueError: si el carretó està buit, si no hi ha stock suficient, o si falten dades d'usuari
        Exception: si hi ha un error al crear la comanda
    """
    import sqlite3
    
    if not cart:
        raise ValueError("El carretó està buit")
    
    with sqlite3.connect(db_path) as conn:
        try:
            # Valida el stock i calcula el total
            total = 0.0
            for product_id, quantity in cart.items():
                product = Product.get_by_id(int(product_id), db_path)
                if product is None:
                    raise ValueError(f"Producte amb ID {product_id} no trobat")
                if product.stock <= 0:
                    raise ValueError(
                        f"El producte {product.name} està sense stock"
                    )
                if product.stock < quantity:
                    raise ValueError(
                        f"Stock insuficient per a {product.name}: "
                        f"se sol·liciten {quantity} però només hi ha {product.stock}"
                    )
                # Verificar que després de la compra el stock no serà negatiu
                if product.stock - quantity < 0:
                    raise ValueError(
                        f"No es pot comprar {quantity} unitats de {product.name}. "
                        f"Stock disponible: {product.stock}"
                    )
                total += product.price * quantity
            
            # Obté o crea l'usuari
            if user_id is not None:
                # Usuari ja autenticat, només verificar que existeix
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT id FROM UserAccount WHERE id = ?", (user_id,))
                if not cur.fetchone():
                    raise ValueError(f"Usuari amb ID {user_id} no trobat")
            else:
                # No hi ha usuari autenticat, cal crear-lo o obtenir-lo
                if not username or not password or not email:
                    raise ValueError("Falten dades d'usuari. Has d'iniciar sessió o proporcionar les dades de registre.")
                
                user = UserAccount.get_by_username(username, db_path)
                
                if user is None:
                    # Crear nou usuari
                    # NOTA: En producció, s'hauria d'utilitzar bcrypt o argon2
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    user_id = UserAccount.create(username, password_hash, email, db_path)
                else:
                    user_id = user.id
            
            # Crea la comanda (amb ubicació per anàlisi geogràfica / Tableau)
            order_id = Order.create(
                total,
                user_id,
                db_path,
                shipping_city=shipping_city,
                shipping_province=shipping_province,
                shipping_country=shipping_country,
            )
            
            # Crea els elements de la comanda i actualitza l'inventari
            for product_id, quantity in cart.items():
                # Crea OrderItem
                OrderItem.create(order_id, int(product_id), quantity, db_path)
                
                # Actualitza el stock (amb validació final)
                product = Product.get_by_id(int(product_id), db_path)
                new_stock = product.stock - quantity
                if new_stock < 0:
                    raise ValueError(
                        f"Error: el stock de {product.name} no pot ser negatiu. "
                        f"Stock actual: {product.stock}, Quantitat sol·licitada: {quantity}"
                    )
                product.update_stock(new_stock, db_path)
            
            conn.commit()
            return order_id
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al crear la comanda: {str(e)}")

