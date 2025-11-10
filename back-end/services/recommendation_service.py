"""Servei de recomanació de productes basat en filtrado col·laboratiu.

Aquest mòdul implementa un sistema de recomanació que analitza les compres
d'altres usuaris per recomanar productes similars als que ha comprat l'usuari actual.
"""
import sqlite3
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import defaultdict


def get_user_purchased_products(user_id: int, db_path: Path) -> Set[int]:
    """Obté el conjunt de productes que ha comprat un usuari.
    
    Args:
        user_id: ID de l'usuari
        db_path: ruta a la base de dades
        
    Returns:
        Conjunt d'IDs de productes comprats per l'usuari
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT oi.product_id
            FROM OrderItem oi
            JOIN "Order" o ON oi.order_id = o.id
            WHERE o.user_id = ?
        """, (user_id,))
        rows = cur.fetchall()
        return {row[0] for row in rows}


def get_similar_users(user_id: int, db_path: Path, min_common_products: int = 1) -> List[int]:
    """Troba usuaris similars basant-se en productes comprats en comú.
    
    Dos usuaris són similars si han comprat almenys un producte en comú.
    
    Args:
        user_id: ID de l'usuari actual
        db_path: ruta a la base de dades
        min_common_products: mínim nombre de productes en comú per considerar-los similars
        
    Returns:
        Llista d'IDs d'usuaris similars
    """
    user_products = get_user_purchased_products(user_id, db_path)
    
    if not user_products:
        return []
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        # Trobar usuaris que han comprat algun dels productes de l'usuari actual
        placeholders = ','.join('?' * len(user_products))
        cur.execute(f"""
            SELECT DISTINCT o.user_id, COUNT(DISTINCT oi.product_id) as common_count
            FROM OrderItem oi
            JOIN "Order" o ON oi.order_id = o.id
            WHERE o.user_id != ? AND oi.product_id IN ({placeholders})
            GROUP BY o.user_id
            HAVING common_count >= ?
        """, (user_id, *user_products, min_common_products))
        
        rows = cur.fetchall()
        return [row[0] for row in rows]


def get_recommendations(user_id: int, db_path: Path, limit: int = 5) -> List[Tuple[int, int]]:
    """Genera recomanacions de productes per a un usuari.
    
    L'algoritme funciona de la següent manera:
    1. Troba usuaris similars (que han comprat productes en comú)
    2. Troba productes que aquests usuaris similars han comprat però l'usuari actual no
    3. Ordena per freqüència (quants usuaris similars han comprat cada producte)
    4. Retorna els top N productes
    
    Args:
        user_id: ID de l'usuari per al qual generar recomanacions
        db_path: ruta a la base de dades
        limit: nombre màxim de recomanacions a retornar
        
    Returns:
        Llista de tuples (product_id, score) ordenada per score descendent
        on score és el nombre d'usuaris similars que han comprat el producte
    """
    # Obtenir productes que l'usuari ja ha comprat
    user_products = get_user_purchased_products(user_id, db_path)
    
    # Trobar usuaris similars
    similar_users = get_similar_users(user_id, db_path)
    
    if not similar_users:
        return []
    
    # Trobar productes comprats pels usuaris similars que l'usuari actual no ha comprat
    product_scores: Dict[int, int] = defaultdict(int)
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        placeholders = ','.join('?' * len(similar_users))
        cur.execute(f"""
            SELECT oi.product_id, COUNT(DISTINCT o.user_id) as user_count
            FROM OrderItem oi
            JOIN "Order" o ON oi.order_id = o.id
            WHERE o.user_id IN ({placeholders})
            GROUP BY oi.product_id
        """, tuple(similar_users))
        
        rows = cur.fetchall()
        for product_id, user_count in rows:
            # Només recomanar productes que l'usuari no ha comprat
            if product_id not in user_products:
                product_scores[product_id] = user_count
    
    # Ordenar per score descendent i retornar els top N
    sorted_recommendations = sorted(
        product_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return sorted_recommendations[:limit]


def get_popular_products(db_path: Path, limit: int = 5, exclude_product_ids: Set[int] = None) -> List[Tuple[int, int]]:
    """Obté els productes més populars (més comprats).
    
    Útil quan no hi ha suficients dades per a recomanacions personalitzades.
    
    Args:
        db_path: ruta a la base de dades
        limit: nombre màxim de productes a retornar
        exclude_product_ids: conjunt d'IDs de productes a excloure
        
    Returns:
        Llista de tuples (product_id, purchase_count) ordenada per count descendent
    """
    exclude_product_ids = exclude_product_ids or set()
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        if exclude_product_ids:
            placeholders = ','.join('?' * len(exclude_product_ids))
            cur.execute(f"""
                SELECT product_id, SUM(quantity) as total_quantity
                FROM OrderItem
                WHERE product_id NOT IN ({placeholders})
                GROUP BY product_id
                ORDER BY total_quantity DESC
                LIMIT ?
            """, (*exclude_product_ids, limit))
        else:
            cur.execute("""
                SELECT product_id, SUM(quantity) as total_quantity
                FROM OrderItem
                GROUP BY product_id
                ORDER BY total_quantity DESC
                LIMIT ?
            """, (limit,))
        
        rows = cur.fetchall()
        return [(row[0], row[1]) for row in rows]

