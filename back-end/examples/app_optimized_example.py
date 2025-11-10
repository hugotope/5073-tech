"""Exemple d'ús dels components optimitzats en app.py.

Aquest fitxer mostra com actualitzar les rutes de Flask per utilitzar
els nous repositoris i serveis optimitzats.
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pathlib import Path

# Importar els nous components optimitzats
from repositories.product_repository import ProductRepository
from services.cart_service import CartService
from services.cache_service import get_cache, cached
from controllers import order_controller

app = Flask(__name__)
app.secret_key = 'techshop_secret_key_change_in_production'

DB_PATH = Path(__file__).parent.parent / "database" / "db.sqlite3"

# Inicialitzar repositoris i serveis
product_repo = ProductRepository(DB_PATH)
cart_service = CartService(DB_PATH)
cache = get_cache()


# ============================================================================
# EXEMPLE 1: Ruta del carretó optimitzada
# ============================================================================

@app.route('/cart')
def cart():
    """Mostra el carretó actual amb validació de stock."""
    cart_dict = session.get('cart', {})
    
    if not cart_dict:
        return render_template('cart.html', cart_items=[], total=0.0, stock_warnings=[])
    
    # Una sola consulta SQL per obtenir tots els productes!
    cart_items, total = cart_service.get_cart_details(cart_dict)
    
    # Validar stock en temps real
    is_valid, error_msg, invalid_products = cart_service.validate_cart_stock(cart_dict)
    
    stock_warnings = []
    if not is_valid:
        # Crear llista d'advertències per mostrar a l'usuari
        for product_id, available_stock in invalid_products.items():
            stock_warnings.append({
                'product_id': product_id,
                'available_stock': available_stock,
                'message': error_msg
            })
    
    # Convertir CartItem a diccionari per al template
    cart_details = [
        {
            'product': item.product,
            'quantity': item.quantity,
            'subtotal': item.subtotal
        }
        for item in cart_items
    ]
    
    return render_template(
        'cart.html',
        cart_items=cart_details,
        total=total,
        stock_warnings=stock_warnings
    )


# ============================================================================
# EXEMPLE 2: Ruta d'índex amb caché
# ============================================================================

@app.route('/')
def index():
    """Pàgina principal amb productes en caché."""
    # Utilitzar caché per productes (s'invalida quan es modifica stock)
    products = cache.get_or_set(
        key='products:all',
        factory=lambda: product_repo.get_all(),
        ttl_seconds=300  # 5 minuts
    )
    
    # Recomanacions (ja implementat)
    user_id = session.get('user_id', None)
    from controllers import recommendation_controller
    recommended_products = recommendation_controller.get_recommended_products(
        user_id, DB_PATH, limit=5
    )
    
    return render_template(
        'index.html',
        products=products,
        recommended_products=recommended_products
    )


# ============================================================================
# EXEMPLE 3: Actualització de stock amb invalidació de caché
# ============================================================================

@app.route('/update_stock', methods=['POST'])
def update_stock():
    """Actualitza el stock d'un producte i invalida el caché."""
    product_id = request.form.get('product_id')
    new_stock = int(request.form.get('stock', 0))
    
    if product_id:
        # Actualitzar stock
        success = product_repo.update_stock(int(product_id), new_stock)
        
        if success:
            # Invalidar caché de productes
            cache.invalidate_pattern('products:')
            flash('Stock actualitzat correctament', 'success')
        else:
            flash('Error al actualitzar el stock', 'error')
    
    return redirect(url_for('index'))


# ============================================================================
# EXEMPLE 4: Add to cart optimitzat
# ============================================================================

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Afegeix un producte al carretó amb validació optimitzada."""
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        
        if not product_id:
            flash('Error: producte no especificat', 'error')
            return redirect(url_for('index'))
        
        # Validacions
        if quantity <= 0 or quantity > 5:
            flash('Error: la quantitat ha de ser entre 1 i 5 unitats', 'error')
            return redirect(url_for('index'))
        
        # Validar stock (una sola consulta)
        if not product_repo.check_stock(int(product_id), quantity):
            product = product_repo.get_by_id(int(product_id))
            if product:
                flash(f'Stock insuficient. Només hi ha {product.stock} unitat(s)', 'error')
            else:
                flash('El producte no existeix', 'error')
            return redirect(url_for('index'))
        
        # Comprovem límit de 5 unitats al carretó
        cart_items = session.get('cart', {})
        current_qty = cart_items.get(product_id, 0)
        
        if current_qty + quantity > 5:
            flash('Error: no pots afegir més de 5 unitats del mateix producte', 'error')
            return redirect(url_for('cart'))
        
        # Afegir al carretó
        from controllers import cart_controller
        success, message = cart_controller.add_to_cart(product_id, quantity, session)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('cart'))
        
    except ValueError:
        flash('Error: quantitat no vàlida', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error inesperat: {str(e)}', 'error')
        return redirect(url_for('index'))


# ============================================================================
# EXEMPLE 5: Decorador de caché per funcions
# ============================================================================

@cached(ttl_seconds=600, key_prefix="products")
def get_all_products_cached():
    """Funció amb resultats cachejats."""
    return product_repo.get_all()


# Comparació de rendiment:
# - Abans: Product.get_all() -> consulta SQL cada vegada
# - Ara: get_all_products_cached() -> consulta SQL només cada 10 minuts

