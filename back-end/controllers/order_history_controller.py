"""Controlador per al historial de comandes.

Aquest mòdul conté la lògica per obtenir i mostrar el historial
de comandes d'un usuari.
"""
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path
from models import Order, OrderItem, Product, UserAccount


def get_user_orders(user_id: int, db_path: Path) -> List[Dict]:
    """Obté totes les comandes d'un usuari amb els seus detalls.
    
    Args:
        user_id: ID de l'usuari
        db_path: ruta a la base de dades
        
    Returns:
        Llista de diccionaris amb les dades de cada comanda
    """
    orders = []
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Obtenir totes les comandes de l'usuari ordenades per data (més recents primer)
        cur.execute(
            "SELECT * FROM \"Order\" WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        order_rows = cur.fetchall()
        
        for order_row in order_rows:
            order = Order(**dict(order_row))
            
            # Obtenir els items de la comanda
            order_items = OrderItem.get_by_order_id(order.id, db_path)
            items_details = []
            
            for item in order_items:
                product = Product.get_by_id(item.product_id, db_path)
                if product:
                    items_details.append({
                        'product': product,
                        'quantity': item.quantity,
                        'unit_price': product.price,
                        'subtotal': product.price * item.quantity
                    })
            
            orders.append({
                'order': order,
                'order_items': items_details,  # Renombrado para evitar conflicto con dict.items()
                'total': order.total,
                'item_count': len(items_details)
            })
    
    return orders


def get_order_count(user_id: int, db_path: Path) -> int:
    """Obté el nombre total de comandes d'un usuari.
    
    Args:
        user_id: ID de l'usuari
        db_path: ruta a la base de dades
        
    Returns:
        Nombre de comandes
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM \"Order\" WHERE user_id = ?", (user_id,))
        return cur.fetchone()[0]
