"""Aplicació principal de TechShop utilitzant Flask.

Aquesta aplicació segueix el patró MVC i l'arquitectura en tres capes:
- Models: accés a dades (models.py)
- Services: lògica de negoci (services/)
- Controllers: controladors i rutes (controllers/)
- Templates: plantilles HTML
- Static: fitxers CSS/JS

Regles implementades:
- No barregar codi HTML amb consultes SQL o lògica de negoci
- Tots els accessos a la base de dades es fan a través de funcions específiques
- No superar les 5 unitats per producte al carretó
- Validar sempre les dades rebudes des del client abans de processar-les
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path

# Importem models
from models import Product, Order, OrderItem, UserAccount
from controllers import cart_controller
from controllers import order_controller
from controllers import recommendation_controller
from controllers import auth_controller

app = Flask(__name__)
app.secret_key = 'techshop_secret_key_change_in_production'  # IMPORTANT: canviar en producció

# Configuració de la base de dades
DB_PATH = Path(__file__).parent / "database" / "db.sqlite3"


@app.route('/')
def index():
    """Pàgina principal que mostra la llista de productes i recomanacions."""
    products = Product.get_all(DB_PATH)
    
    # Obtenir recomanacions
    # Intentem obtenir user_id de la sessió si existeix
    user_id = session.get('user_id', None)
    recommended_products = recommendation_controller.get_recommended_products(
        user_id, DB_PATH, limit=5
    )
    
    return render_template('index.html', 
                         products=products, 
                         recommended_products=recommended_products)


@app.route('/cart')
def cart():
    """Mostra el carretó actual."""
    cart_items = session.get('cart', {})
    products = Product.get_all(DB_PATH)
    cart_details = []
    total = 0
    
    for product_id, quantity in cart_items.items():
        product = next((p for p in products if p.id == int(product_id)), None)
        if product:
            cart_details.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total += product.price * quantity
    
    return render_template('cart.html', cart_items=cart_details, total=total)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Afegeix un producte al carretó.
    
    Validacions:
    - La quantitat ha de ser un enter positiu
    - No superar el límit de 5 unitats del mateix producte al carretó
    - Comprovar que hi ha stock suficient
    """
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
        
        # Comprovem stock
        stock_valid, error_msg = cart_controller.validate_stock(product_id, quantity, DB_PATH)
        if not stock_valid:
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        # Comprovem límit de 5 unitats al carretó
        cart_items = session.get('cart', {})
        current_qty = cart_items.get(product_id, 0)
        
        if current_qty + quantity > 5:
            flash(f'Error: no pots afegir més de 5 unitats del mateix producte al carretó', 'error')
            return redirect(url_for('cart'))
        
        # Afegim al carretó
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


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """Elimina un producte del carretó."""
    try:
        product_id = request.form.get('product_id')
        
        if not product_id:
            flash('Error: producte no especificat', 'error')
            return redirect(url_for('cart'))
        
        success, message = cart_controller.remove_from_cart(product_id, session)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('cart'))
        
    except Exception as e:
        flash(f'Error inesperat: {str(e)}', 'error')
        return redirect(url_for('cart'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Pàgina d'inici de sessió.
    
    GET: mostra el formulari de login
    POST: processa l'inici de sessió
    """
    # Si l'usuari ja està autenticat, redirigir a l'índex
    if session.get('user_id'):
        flash('Ja estàs autenticat', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('login.html')
    
    else:  # POST
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Has d\'introduir nom d\'usuari i contrasenya', 'error')
            return redirect(url_for('login'))
        
        success, message, user = auth_controller.login_user(username, password, DB_PATH)
        
        if success and user:
            # Guardar dades de l'usuari a la sessió
            session['user_id'] = user.id
            session['username'] = user.username
            flash(message, 'success')
            
            # Redirigir a la pàgina que volia visitar o a l'índex
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        else:
            flash(message, 'error')
            return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Pàgina de registre d'usuaris.
    
    GET: mostra el formulari de registre
    POST: processa el registre
    """
    # Si l'usuari ja està autenticat, redirigir a l'índex
    if session.get('user_id'):
        flash('Ja estàs autenticat', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('register.html')
    
    else:  # POST
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validació de confirmació de contrasenya
        if password != confirm_password:
            flash('Les contrasenyes no coincideixen', 'error')
            return redirect(url_for('register'))
        
        # Registrar l'usuari
        success, message = auth_controller.register_user(username, password, email, DB_PATH)
        
        if success:
            flash(message, 'success')
            # Autenticar automàticament després del registre
            success_login, _, user = auth_controller.login_user(username, password, DB_PATH)
            if success_login and user:
                session['user_id'] = user.id
                session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash(message, 'error')
            return redirect(url_for('register'))


@app.route('/logout')
def logout():
    """Tanca la sessió de l'usuari."""
    username = session.get('username', 'Usuari')
    session.clear()
    flash(f'Has tancat sessió correctament. Fins aviat, {username}!', 'info')
    return redirect(url_for('index'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Pàgina de finalització de compra.
    
    GET: mostra el formulari de checkout
    POST: processa la comanda
    """
    if request.method == 'GET':
        cart_items = session.get('cart', {})
        
        if not cart_items:
            flash('El carretó està buit', 'info')
            return redirect(url_for('cart'))
        
        products = Product.get_all(DB_PATH)
        cart_details = []
        total = 0
        
        for product_id, quantity in cart_items.items():
            product = next((p for p in products if p.id == int(product_id)), None)
            if product:
                cart_details.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': product.price * quantity
                })
                total += product.price * quantity
        
        return render_template('checkout.html', cart_items=cart_details, total=total)
    
    else:  # POST
        # Obtenim les dades del formulari
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        
        # Validacions del servidor
        errors = []
        if len(username) < 4 or len(username) > 20:
            errors.append('El nom d\'usuari ha de tenir entre 4 i 20 caràcters')
        if len(password) < 8:
            errors.append('La contrasenya ha de tenir com a mínim 8 caràcters')
        if not email or '@' not in email:
            errors.append('Correu electrònic no vàlid')
        if not shipping_address:
            errors.append('Has d\'introduir una adreça d\'enviament')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('checkout'))
        
        # Processem la comanda
        cart_items = session.get('cart', {})
        
        if not cart_items:
            flash('El carretó està buit', 'error')
            return redirect(url_for('index'))
        
        try:
            # Crear usuari i comanda
            order_id = order_controller.create_order(
                cart_items,
                username=username,
                password=password,
                email=email,
                db_path=DB_PATH
            )
            
            # Guardar user_id a la sessió per a recomanacions
            user = UserAccount.get_by_username(username, DB_PATH)
            if user:
                session['user_id'] = user.id
                session['username'] = username
            
            # Netegem el carretó
            session['cart'] = {}
            session.pop('cart', None)
            
            flash(f'Comanda realitzada amb èxit! ID de comanda: {order_id}', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error al processar la comanda: {str(e)}', 'error')
            return redirect(url_for('checkout'))


if __name__ == '__main__':
    # Assegurar que la base de dades existeix
    if not DB_PATH.exists():
        import sys
        sys.path.append(str(Path(__file__).parent / 'database'))
        from init_db import init_db
        init_db()
    
    app.run(debug=True, port=5001)

