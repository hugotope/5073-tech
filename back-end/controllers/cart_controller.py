"""Controlador per al carretó de compres.

Aquest mòdul conté la lògica de negoci relacionada amb el carretó de compres,
incloent les funcions add_to_cart, remove_from_cart i validate_stock.

Regles de negoci implementades:
- No superar les 5 unitats per producte al carretó
- Validar stock disponible abans d'afegir productes
- La quantitat ha de ser un enter positiu
"""
from typing import Tuple, Optional
from pathlib import Path
from models import Product


def add_to_cart(product_id: str, quantity: int, session) -> Tuple[bool, str]:
    """Afegeix un producte al carretó de la sessió.
    
    Args:
        product_id: identificador del producte (com a string)
        quantity: quantitat a afegir
        session: objecte de sessió de Flask
        
    Returns:
        Tupla (èxit, missatge)
        
    Raises:
        ValueError: si la quantitat no és vàlida
    """
    if quantity <= 0:
        return False, "La quantitat ha de ser major que 0"
    
    if quantity > 5:
        return False, "No pots afegir més de 5 unitats"
    
    # Obtenim o creem el carretó
    cart = session.get('cart', {})
    
    # Comprovem el límit total de 5 unitats
    current_qty = cart.get(product_id, 0)
    if current_qty + quantity > 5:
        return False, "No pots tenir més de 5 unitats d'aquest producte al carretó"
    
    # Afegim o actualitzem la quantitat
    cart[product_id] = current_qty + quantity
    session['cart'] = cart
    
    return True, f"S'han afegit {quantity} unitat(s) al carretó"


def remove_from_cart(product_id: str, session) -> Tuple[bool, str]:
    """Elimina un producte del carretó de la sessió.
    
    Args:
        product_id: identificador del producte a eliminar
        session: objecte de sessió de Flask
        
    Returns:
        Tupla (èxit, missatge)
    """
    cart = session.get('cart', {})
    
    if product_id not in cart:
        return False, "Aquest producte no està al carretó"
    
    # Eliminem el producte del carretó
    del cart[product_id]
    session['cart'] = cart
    
    return True, "Producte eliminat del carretó"


def validate_stock(product_id: str, quantity: int, db_path: Path) -> Tuple[bool, Optional[str]]:
    """Valida que hi ha stock suficient per a una quantitat donada d'un producte.
    
    Args:
        product_id: identificador del producte
        quantity: quantitat necessària
        db_path: ruta a la base de dades
        
    Returns:
        Tupla (vàlid, missatge_d'error o None)
    """
    try:
        product = Product.get_by_id(int(product_id), db_path)
        
        if product is None:
            return False, "El producte no existeix"
        
        if product.stock < quantity:
            return False, f"Stock insuficient. Només hi ha {product.stock} unitat(s) disponible(s)"
        
        return True, None
        
    except ValueError:
        return False, "ID de producte no vàlid"
    except Exception as e:
        return False, f"Error al validar el stock: {str(e)}"


def get_cart_total(cart: dict, db_path: Path) -> float:
    """Calcula el total del carretó basant-se en els productes i quantitats.
    
    Args:
        cart: diccionari amb product_id -> quantity
        db_path: ruta a la base de dades
        
    Returns:
        Total del carretó
    """
    total = 0.0
    
    for product_id, quantity in cart.items():
        product = Product.get_by_id(int(product_id), db_path)
        if product:
            total += product.price * quantity
    
    return total

