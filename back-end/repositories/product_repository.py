"""Repositori per a l'accés a dades de productes.

Aquest repositori centralitza totes les operacions de base de dades
relacionades amb productes, proporcionant una interfície neta i optimitzada.
"""
from typing import List, Optional, Set
from pathlib import Path
from dataclasses import dataclass

from repositories.base_repository import BaseRepository


@dataclass
class Product:
    """Model que representa un producte."""
    id: int
    name: str
    price: float
    stock: int


class ProductRepository(BaseRepository):
    """Repositori per a operacions de productes."""
    
    def get_all(self) -> List[Product]:
        """Obté tots els productes de la base de dades.
        
        Returns:
            Llista de productes ordenats per nom
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Product ORDER BY name")
            rows = cur.fetchall()
            return [Product(**dict(row)) for row in rows]
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Obté un producte per ID.
        
        Args:
            product_id: identificador del producte
            
        Returns:
            Producte o None si no existeix
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Product WHERE id = ?", (product_id,))
            row = cur.fetchone()
            if row:
                return Product(**dict(row))
            return None
    
    def get_by_ids(self, product_ids: List[int]) -> List[Product]:
        """Obté múltiples productes per les seves IDs.
        
        Aquest mètode optimitza la consulta usant IN en lloc de
        múltiples consultes individuals (evita el problema N+1).
        
        Args:
            product_ids: llista d'IDs de productes
            
        Returns:
            Llista de productes trobats (pot ser buida si cap ID existeix)
        """
        if not product_ids:
            return []
        
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Crear placeholders per a la consulta IN
            placeholders = ','.join('?' * len(product_ids))
            cur.execute(
                f"SELECT * FROM Product WHERE id IN ({placeholders})",
                tuple(product_ids)
            )
            rows = cur.fetchall()
            return [Product(**dict(row)) for row in rows]
    
    def get_available(self, min_stock: int = 1) -> List[Product]:
        """Obté productes amb stock disponible.
        
        Args:
            min_stock: stock mínim requerit (per defecte 1)
            
        Returns:
            Llista de productes amb stock >= min_stock
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM Product WHERE stock >= ? ORDER BY name",
                (min_stock,)
            )
            rows = cur.fetchall()
            return [Product(**dict(row)) for row in rows]
    
    def update_stock(self, product_id: int, new_stock: int) -> bool:
        """Actualitza el stock d'un producte.
        
        Args:
            product_id: identificador del producte
            new_stock: nou valor de stock
            
        Returns:
            True si s'ha actualitzat correctament, False altrament
        """
        try:
            with self.transaction() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE Product SET stock = ? WHERE id = ?",
                    (new_stock, product_id)
                )
                return cur.rowcount > 0
        except Exception:
            return False
    
    def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """Disminueix el stock d'un producte (operació atòmica).
        
        Aquest mètode és més segur que update_stock perquè evita
        condicions de carrera usant una operació atòmica.
        
        Args:
            product_id: identificador del producte
            quantity: quantitat a disminuir
            
        Returns:
            True si s'ha disminuït correctament, False si no hi ha stock suficient
        """
        try:
            with self.transaction() as conn:
                cur = conn.cursor()
                # Verificar stock abans de disminuir
                cur.execute("SELECT stock FROM Product WHERE id = ?", (product_id,))
                row = cur.fetchone()
                if not row or row['stock'] < quantity:
                    return False
                
                # Disminuir stock de forma atòmica
                cur.execute(
                    "UPDATE Product SET stock = stock - ? WHERE id = ? AND stock >= ?",
                    (quantity, product_id, quantity)
                )
                return cur.rowcount > 0
        except Exception:
            return False
    
    def check_stock(self, product_id: int, required_quantity: int) -> bool:
        """Comprova si hi ha stock suficient per a una quantitat donada.
        
        Args:
            product_id: identificador del producte
            required_quantity: quantitat requerida
            
        Returns:
            True si hi ha stock suficient, False altrament
        """
        product = self.get_by_id(product_id)
        return product is not None and product.stock >= required_quantity

