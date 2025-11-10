"""Controlador per a les recomanacions de productes.

Aquest mòdul conté la lògica per obtenir i processar recomanacions
de productes per als usuaris.
"""
from typing import List, Optional
from pathlib import Path
from models import Product
from services.recommendation_service import (
    get_recommendations,
    get_popular_products,
    get_user_purchased_products
)


def get_recommended_products(user_id: Optional[int], db_path: Path, limit: int = 5) -> List[Product]:
    """Obté productes recomanats per a un usuari.
    
    Si l'usuari ha comprat productes, utilitza recomanacions personalitzades.
    Si no, retorna els productes més populars.
    
    Args:
        user_id: ID de l'usuari (None si no està autenticat)
        db_path: ruta a la base de dades
        limit: nombre màxim de recomanacions
        
    Returns:
        Llista de productes recomanats
    """
    if user_id is None:
        # Si no hi ha usuari, retornar productes populars
        popular = get_popular_products(db_path, limit=limit)
        recommended_ids = [product_id for product_id, _ in popular]
    else:
        # Intentar obtenir recomanacions personalitzades
        recommendations = get_recommendations(user_id, db_path, limit=limit)
        
        if recommendations:
            recommended_ids = [product_id for product_id, _ in recommendations]
        else:
            # Si no hi ha recomanacions personalitzades, usar productes populars
            # excloent els que l'usuari ja ha comprat
            user_products = get_user_purchased_products(user_id, db_path)
            popular = get_popular_products(db_path, limit=limit, exclude_product_ids=user_products)
            recommended_ids = [product_id for product_id, _ in popular]
    
    # Obtenir els objectes Product
    recommended_products = []
    for product_id in recommended_ids:
        product = Product.get_by_id(product_id, db_path)
        if product and product.stock > 0:  # Només recomanar productes amb stock
            recommended_products.append(product)
    
    return recommended_products

