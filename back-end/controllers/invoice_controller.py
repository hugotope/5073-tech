"""Controlador per a la generació de factures.

Aquest mòdul conté la lògica per generar factures a partir de comandes,
incloent la funció get_invoice_data que obté tots els detalls necessaris
per mostrar una factura completa.
"""
import sqlite3
from typing import Dict, List, Optional
from pathlib import Path
from models import Order, OrderItem, Product, UserAccount


def get_invoice_data(order_id: int, db_path: Path) -> Optional[Dict]:
    """Obté tots els detalls d'una comanda per generar la factura.
    
    Args:
        order_id: ID de la comanda
        db_path: ruta a la base de dades
        
    Returns:
        Diccionari amb tots els detalls de la factura o None si la comanda no existeix
    """
    # Obtenir la comanda
    order = Order.get_by_id(order_id, db_path)
    if order is None:
        return None
    
    # Obtenir l'usuari
    user = None
    if order.user_id:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM UserAccount WHERE id = ?", (order.user_id,))
            row = cur.fetchone()
            if row:
                user = UserAccount(**dict(row))
    
    # Obtenir els elements de la comanda amb els detalls dels productes
    order_items = OrderItem.get_by_order_id(order_id, db_path)
    invoice_items = []
    
    for item in order_items:
        product = Product.get_by_id(item.product_id, db_path)
        if product:
            invoice_items.append({
                'product': product,
                'quantity': item.quantity,
                'unit_price': product.price,
                'subtotal': product.price * item.quantity
            })
    
    # Calcular total (per si hi ha alguna discrepància)
    calculated_total = sum(item['subtotal'] for item in invoice_items)
    
    return {
        'order': order,
        'user': user,
        'invoice_items': invoice_items,  # Renombrado para evitar conflicto con dict.items()
        'total': order.total,
        'calculated_total': calculated_total,
        'order_id': order_id
    }


def format_invoice_number(order_id: int) -> str:
    """Formata el número de factura amb un format estàndard.
    
    Args:
        order_id: ID de la comanda
        
    Returns:
        Número de factura formatat (ex: FACT-2025-0001)
    """
    from datetime import datetime
    year = datetime.now().year
    return f"FACT-{year}-{order_id:04d}"

