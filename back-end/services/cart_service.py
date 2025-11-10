"""Servei optimitzat per a la gestió del carretó.

Aquest servei proporciona funcionalitats optimitzades per al carretó,
incloent consultes batch i validació eficient de stock.
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from repositories.product_repository import ProductRepository, Product


@dataclass
class CartItem:
    """Representa un element del carretó amb informació completa."""
    product: Product
    quantity: int
    
    @property
    def subtotal(self) -> float:
        """Calcula el subtotal d'aquest element."""
        return self.product.price * self.quantity


class CartService:
    """Servei per a la gestió del carretó amb optimitzacions."""
    
    def __init__(self, db_path: Path):
        """Inicialitza el servei de carretó.
        
        Args:
            db_path: ruta a la base de dades
        """
        self.product_repo = ProductRepository(db_path)
    
    def get_cart_details(self, cart: Dict[str, int]) -> Tuple[List[CartItem], float]:
        """Obté els detalls del carretó de forma optimitzada.
        
        En lloc de fer una consulta per cada producte (problema N+1),
        fa una sola consulta amb IN per obtenir tots els productes.
        
        Args:
            cart: diccionari amb product_id -> quantity
            
        Returns:
            Tupla (llista de CartItem, total del carretó)
        """
        if not cart:
            return [], 0.0
        
        # Obtenir tots els IDs de productes del carretó
        product_ids = [int(pid) for pid in cart.keys()]
        
        # Una sola consulta per obtenir tots els productes
        products = self.product_repo.get_by_ids(product_ids)
        
        # Crear diccionari per accés ràpid per ID
        products_dict = {p.id: p for p in products}
        
        # Construir llista de CartItem i calcular total
        cart_items = []
        total = 0.0
        
        for product_id_str, quantity in cart.items():
            product_id = int(product_id_str)
            product = products_dict.get(product_id)
            
            if product:
                cart_item = CartItem(product=product, quantity=quantity)
                cart_items.append(cart_item)
                total += cart_item.subtotal
        
        return cart_items, total
    
    def validate_cart_stock(self, cart: Dict[str, int]) -> Tuple[bool, Optional[str], Dict[int, int]]:
        """Valida el stock de tots els productes del carretó.
        
        Retorna informació sobre quins productes tenen problemes de stock.
        
        Args:
            cart: diccionari amb product_id -> quantity
            
        Returns:
            Tupla (vàlid, missatge_error, diccionari_productes_invàlids)
            on diccionari_productes_invàlids és {product_id: stock_disponible}
        """
        if not cart:
            return True, None, {}
        
        product_ids = [int(pid) for pid in cart.keys()]
        products = self.product_repo.get_by_ids(product_ids)
        products_dict = {p.id: p for p in products}
        
        invalid_products = {}
        
        for product_id_str, quantity in cart.items():
            product_id = int(product_id_str)
            product = products_dict.get(product_id)
            
            if not product:
                invalid_products[product_id] = 0
            elif product.stock < quantity:
                invalid_products[product_id] = product.stock
        
        if invalid_products:
            # Construir missatge d'error descriptiu
            error_parts = []
            for pid, available_stock in invalid_products.items():
                product = products_dict.get(pid)
                product_name = product.name if product else f"Producte ID {pid}"
                if available_stock == 0:
                    error_parts.append(f"{product_name} ja no està disponible")
                else:
                    error_parts.append(
                        f"{product_name}: només hi ha {available_stock} unitat(s) disponible(s)"
                    )
            
            error_msg = "Problemes de stock: " + "; ".join(error_parts)
            return False, error_msg, invalid_products
        
        return True, None, {}
    
    def get_cart_summary(self, cart: Dict[str, int]) -> Dict:
        """Obté un resum del carretó amb estadístiques.
        
        Args:
            cart: diccionari amb product_id -> quantity
            
        Returns:
            Diccionari amb resum del carretó:
            - item_count: nombre d'elements diferents
            - total_items: quantitat total d'unitats
            - total_price: preu total
            - is_valid: si el carretó és vàlid
        """
        cart_items, total = self.get_cart_details(cart)
        is_valid, error_msg, _ = self.validate_cart_stock(cart)
        
        total_items = sum(item.quantity for item in cart_items)
        
        return {
            'item_count': len(cart_items),
            'total_items': total_items,
            'total_price': total,
            'is_valid': is_valid,
            'error_message': error_msg
        }

