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
                if product.stock < quantity:
                    raise ValueError(
                        f"Stock insuficient per a {product.name}: "
                        f"se sol·liciten {quantity} però només hi ha {product.stock}"
                    )
                total += product.price * quantity
            
            # Crea o obté l'usuari
            user = UserAccount.get_by_username(username, db_path)
            
            if user is None:
                # Crear nou usuari
                # NOTA: En producció, s'hauria d'utilitzar bcrypt o argon2
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                user_id = UserAccount.create(username, password_hash, email, db_path)
            else:
                user_id = user.id
            
            # Crea la comanda
            order_id = Order.create(total, user_id, db_path)
            
            # Crea els elements de la comanda i actualitza l'inventari
            for product_id, quantity in cart.items():
                # Crea OrderItem
                OrderItem.create(order_id, int(product_id), quantity, db_path)
                
                # Actualitza el stock
                product = Product.get_by_id(int(product_id), db_path)
                new_stock = product.stock - quantity
                product.update_stock(new_stock, db_path)
            
            conn.commit()
            return order_id
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al crear la comanda: {str(e)}")

