"""Exemples d'ús dels components optimitzats.

Aquest fitxer mostra com utilitzar els nous repositoris i serveis
per millorar el rendiment i mantenibilitat del codi.
"""
from pathlib import Path
from repositories.product_repository import ProductRepository
from services.cart_service import CartService

# Configuració
DB_PATH = Path(__file__).parent.parent / "database" / "db.sqlite3"

# ============================================================================
# EXEMPLE 1: Ús del Repositori de Productes
# ============================================================================

def example_product_repository():
    """Exemple d'ús del repositori de productes."""
    repo = ProductRepository(DB_PATH)
    
    # Obtenir un producte per ID
    product = repo.get_by_id(1)
    if product:
        print(f"Producte: {product.name}, Preu: {product.price}€")
    
    # Obtenir múltiples productes (optimitzat!)
    product_ids = [1, 2, 3, 4, 5]
    products = repo.get_by_ids(product_ids)  # Una sola consulta SQL
    print(f"S'han trobat {len(products)} productes")
    
    # Obtenir només productes amb stock
    available_products = repo.get_available(min_stock=1)
    print(f"Productes disponibles: {len(available_products)}")
    
    # Disminuir stock de forma segura (atòmica)
    success = repo.decrease_stock(product_id=1, quantity=2)
    if success:
        print("Stock disminuït correctament")
    else:
        print("No hi ha stock suficient")


# ============================================================================
# EXEMPLE 2: Ús del Servei de Carretó Optimitzat
# ============================================================================

def example_cart_service():
    """Exemple d'ús del servei de carretó optimitzat."""
    cart_service = CartService(DB_PATH)
    
    # Simular un carretó
    cart = {
        "1": 2,  # 2 unitats del producte 1
        "2": 1,  # 1 unitat del producte 2
        "3": 3,  # 3 unitats del producte 3
    }
    
    # Obtenir detalls del carretó (una sola consulta SQL!)
    cart_items, total = cart_service.get_cart_details(cart)
    
    print(f"Carretó amb {len(cart_items)} productes diferents")
    print(f"Total: {total:.2f}€")
    
    for item in cart_items:
        print(f"  - {item.product.name}: {item.quantity}x {item.product.price}€ = {item.subtotal}€")
    
    # Validar stock de tot el carretó
    is_valid, error_msg, invalid_products = cart_service.validate_cart_stock(cart)
    
    if is_valid:
        print("✓ El carretó és vàlid")
    else:
        print(f"✗ Errors: {error_msg}")
        print(f"  Productes amb problemes: {invalid_products}")
    
    # Obtenir resum del carretó
    summary = cart_service.get_cart_summary(cart)
    print(f"\nResum del carretó:")
    print(f"  - Elements diferents: {summary['item_count']}")
    print(f"  - Unitats totals: {summary['total_items']}")
    print(f"  - Preu total: {summary['total_price']:.2f}€")
    print(f"  - Vàlid: {summary['is_valid']}")


# ============================================================================
# EXEMPLE 3: Comparació de Rendiment
# ============================================================================

def performance_comparison():
    """Compara el rendiment entre l'aproximació antiga i la nova."""
    import time
    
    cart = {str(i): 1 for i in range(1, 11)}  # Carretó amb 10 productes
    
    # Mètode antic (N+1 queries)
    print("Mètode antic (N+1 queries):")
    start = time.time()
    from models import Product as OldProduct
    old_products = []
    for product_id in cart.keys():
        product = OldProduct.get_by_id(int(product_id), DB_PATH)
        if product:
            old_products.append(product)
    old_time = time.time() - start
    print(f"  Temps: {old_time:.4f}s")
    print(f"  Consultes SQL: {len(cart)}")
    
    # Mètode nou (1 query)
    print("\nMètode nou (1 query):")
    start = time.time()
    cart_service = CartService(DB_PATH)
    new_items, total = cart_service.get_cart_details(cart)
    new_time = time.time() - start
    print(f"  Temps: {new_time:.4f}s")
    print(f"  Consultes SQL: 1")
    
    print(f"\nMillora: {old_time/new_time:.2f}x més ràpid")


if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLE 1: Repositori de Productes")
    print("=" * 60)
    example_product_repository()
    
    print("\n" + "=" * 60)
    print("EXEMPLE 2: Servei de Carretó")
    print("=" * 60)
    example_cart_service()
    
    print("\n" + "=" * 60)
    print("EXEMPLE 3: Comparació de Rendiment")
    print("=" * 60)
    performance_comparison()

