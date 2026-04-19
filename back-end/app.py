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
from pathlib import Path
import os

from dotenv import load_dotenv

# Carregar .env des de la arrel del projecte o des de back-end
_load_env = load_dotenv(Path(__file__).parent.parent / ".env") or load_dotenv(Path(__file__).parent / ".env")

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3

# Importem models
from models import Product, Order, OrderItem, UserAccount, Category
from controllers import cart_controller
from controllers import order_controller
from controllers import recommendation_controller
from controllers import auth_controller
from controllers import invoice_controller
from controllers import order_history_controller
from services.sheets_sync_service import (
    sync_recommended_products_to_sheets,
    sync_order_invoice_to_sheets,
    is_sheets_configured,
)

app = Flask(__name__)
app.secret_key = 'techshop_secret_key_change_in_production'  # IMPORTANT: canviar en producció

# Configuració de la base de dades
DB_PATH = Path(__file__).parent / "database" / "db.sqlite3"


@app.context_processor
def inject_global_template_vars():
    """Inyecta en tots els templates: Google Sheets, categories (per navbar) i paràmetres de cerca."""
    data = {"sheets_configured": is_sheets_configured()}
    try:
        data["navbar_categories"] = Category.get_all(DB_PATH)
    except sqlite3.OperationalError:
        data["navbar_categories"] = []
    data["navbar_q"] = request.args.get("q", "").strip() if request else ""
    data["navbar_category"] = request.args.get("category", "") if request else ""
    return data


@app.route('/')
def index():
    """Pàgina principal que mostra la llista de productes i recomanacions."""
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('q', '').strip() or request.args.get('search', '').strip()
    try:
        categories = Category.get_all(DB_PATH)
        category_by_id = {c.id: c for c in categories}
        current_category = Category.get_by_id(category_id, DB_PATH) if category_id else None
        products = Product.get_all(
            DB_PATH, category_id=category_id, search_query=search_query or None
        )
    except sqlite3.OperationalError:
        categories = []
        category_by_id = {}
        current_category = None
        products = Product.get_all(DB_PATH)

    user_id = session.get('user_id', None)
    recommended_products = recommendation_controller.get_recommended_products(
        user_id, DB_PATH, limit=5
    )

    return render_template(
        'index.html',
        products=products,
        recommended_products=recommended_products,
        categories=categories,
        category_by_id=category_by_id,
        current_category=current_category,
        search_query=search_query,
    )


@app.route('/sync-recommendations-sheets', methods=['GET', 'POST'])
def sync_recommendations_sheets():
    """
    Sincronitza els productes recomanats i el seu stock amb Google Sheets.
    Es mostren els recomanats per l'usuari actual (o els populars si no hi ha sessió).
    """
    user_id = session.get('user_id', None)
    recommended_products = recommendation_controller.get_recommended_products(
        user_id, DB_PATH, limit=50
    )
    rows = [(p.id, p.name, p.price, p.stock) for p in recommended_products]
    success, message, url = sync_recommended_products_to_sheets(rows, DB_PATH, create_if_missing=True)
    if success:
        flash(message, 'success')
        if url:
            flash(f"Obre el document: {url}", 'info')
    else:
        flash(message, 'error')
    # Query param per mostrar un avís explícit a la UI després de la redirecció
    return redirect(url_for('index', sheets_sync='1' if success else '0'))


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


@app.route('/order-history')
def order_history():
    """Mostra el historial de comandes de l'usuari autenticat."""
    user_id = session.get('user_id')
    
    if not user_id:
        flash('Has d\'iniciar sessió per veure el teu historial de comandes', 'info')
        return redirect(url_for('login'))
    
    # Obtenir el historial de comandes
    orders = order_history_controller.get_user_orders(user_id, DB_PATH)
    order_count = order_history_controller.get_order_count(user_id, DB_PATH)
    
    # Obtenir informació de l'usuari
    user = UserAccount.get_by_username(session.get('username', ''), DB_PATH)
    
    return render_template('order_history.html', 
                         orders=orders,
                         order_count=order_count,
                         user=user)


@app.route('/invoice/<int:order_id>')
def invoice(order_id):
    """Mostra la factura d'una comanda.
    
    Args:
        order_id: ID de la comanda
    """
    # Obtenir les dades de la factura
    invoice_data = invoice_controller.get_invoice_data(order_id, DB_PATH)
    
    if invoice_data is None:
        flash('La comanda no existeix', 'error')
        return redirect(url_for('index'))
    
    # Verificar que l'usuari autenticat és el propietari de la comanda (opcional)
    if session.get('user_id') and invoice_data['user']:
        if session.get('user_id') != invoice_data['user'].id:
            flash('No tens permís per veure aquesta factura', 'error')
            return redirect(url_for('index'))
    
    # Generar número de factura
    invoice_number = invoice_controller.format_invoice_number(order_id)
    current_year = datetime.now().year
    
    return render_template('invoice.html', 
                         invoice_data=invoice_data,
                         invoice_number=invoice_number,
                         current_year=current_year)


@app.route('/invoice/<int:order_id>/export-sheets', methods=['GET'])
def export_invoice_to_sheets(order_id):
    """Exporta la comanda (línies comprades) a Google Sheets (append, sense esborrar recomanacions)."""
    if not is_sheets_configured():
        flash("Google Sheets no està configurat (falta GOOGLE_APPLICATION_CREDENTIALS).", "error")
        return redirect(url_for('invoice', order_id=order_id))

    invoice_data = invoice_controller.get_invoice_data(order_id, DB_PATH)
    if invoice_data is None:
        flash('La comanda no existeix', 'error')
        return redirect(url_for('index'))

    # Permisos:
    # - Si la comanda té usuari: només el propietari autenticat
    # - Si no hi ha sessió: només just després del checkout (last_invoice_order_id)
    uid = session.get('user_id')
    user = invoice_data.get('user')
    last_oid = session.get('last_invoice_order_id')

    if user:
        if not uid or int(uid) != int(user.id):
            flash('Has d\'iniciar sessió com a propietari de la comanda per exportar-la a Google Sheets.', 'error')
            return redirect(url_for('login'))
    else:
        if not last_oid or int(last_oid) != int(order_id):
            flash('No tens permís per exportar aquesta comanda', 'error')
            return redirect(url_for('index'))

    success, message, url = sync_order_invoice_to_sheets(invoice_data, create_if_missing=True)
    if success:
        flash(message, 'success')
        if url:
            flash(f"Obre el document: {url}", 'info')
    else:
        flash(message, 'error')

    return redirect(url_for('invoice', order_id=order_id, sheets_sync='1' if success else '0'))


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
        
        # Obtenir informació de l'usuari si està autenticat
        user = None
        user_id = session.get('user_id')
        if user_id:
            user = UserAccount.get_by_username(session.get('username', ''), DB_PATH)
        
        return render_template('checkout.html', 
                             cart_items=cart_details, 
                             total=total,
                             user=user,
                             is_authenticated=bool(user_id))
    
    else:  # POST
        # Obtenim les dades del formulari (adreça i ubicació per Tableau/mapes)
        shipping_address = request.form.get('shipping_address', '').strip()
        shipping_city = request.form.get('shipping_city', '').strip() or None
        shipping_province = request.form.get('shipping_province', '').strip() or None
        shipping_country = request.form.get('shipping_country', '').strip() or None

        # Verificar si l'usuari està autenticat
        user_id = session.get('user_id')
        is_authenticated = bool(user_id)
        
        # Si no està autenticat, obtenir dades del formulari
        if not is_authenticated:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            email = request.form.get('email', '').strip()
            
            # Validacions del servidor per a usuaris no autenticats
            errors = []
            if len(username) < 4 or len(username) > 20:
                errors.append('El nom d\'usuari ha de tenir entre 4 i 20 caràcters')
            if len(password) < 8:
                errors.append('La contrasenya ha de tenir com a mínim 8 caràcters')
            if not email or '@' not in email:
                errors.append('Correu electrònic no vàlid')
        else:
            username = session.get('username', '')
            password = None
            email = None
        
        # Validació de l'adreça d'enviament (sempre necessària)
        errors = errors if not is_authenticated else []
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
            # Crear comanda (amb ubicació per mapes / Tableau Story)
            if is_authenticated:
                order_id = order_controller.create_order(
                    cart_items,
                    db_path=DB_PATH,
                    user_id=user_id,
                    shipping_city=shipping_city,
                    shipping_province=shipping_province,
                    shipping_country=shipping_country,
                )
            else:
                order_id = order_controller.create_order(
                    cart_items,
                    db_path=DB_PATH,
                    username=username,
                    password=password,
                    email=email,
                    shipping_city=shipping_city,
                    shipping_province=shipping_province,
                    shipping_country=shipping_country,
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
            # Permet exportar la comanda a Sheets just després de la compra (sense exposar IDs aleatoris)
            session['last_invoice_order_id'] = int(order_id)
            # Redirigir a la factura
            return redirect(url_for('invoice', order_id=order_id))

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

