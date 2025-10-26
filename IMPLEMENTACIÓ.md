# TechShop - Documentació de la Implementació

## 📋 Resum de la Implementació

Aquest document descriu tot el que s'ha implementat segons els requisits de la Pràctica TechShop.

## 🏗️ Components Implementats

### 1. Base de Dades (ja existia, s'ha verificat)

✓ Taula `Product` amb camps: id, name, price, stock
✓ Taula `UserAccount` amb camps: id, username, password_hash, email, created_at
✓ Taula `Order` amb camps: id, total, created_at, user_id
✓ Taula `OrderItem` amb camps: id, order_id, product_id, quantity
✓ Relacions i constraints implementades
✓ Script d'inicialització `init_db.py` amb dades d'exemple
✓ Diagrama ER en format DOT

### 2. Models (Capa de Dades)

✅ **models.py** - Conté les classes de dades:
- `Product`: gestiona accés a dades de productes
  - `get_all()`: obté tots els productes
  - `get_by_id()`: obté un producte per ID
  - `update_stock()`: actualitza el stock

- `UserAccount`: gestiona comptes d'usuari
  - `create()`: crea un nou usuari
  - `get_by_username()`: obté un usuari per username

- `Order`: gestiona comandes
  - `create()`: crea una nova comanda

- `OrderItem`: gestiona elements de comandes
  - `create()`: afegeix un element a una comanda

**Responsabilitat**: Tota la lògica d'accés a la base de dades queda encapsulada aquí. No hi ha SQL directe en altres capes.

### 3. Controllers (Capa de Lògica de Negoci)

#### ✅ cart_controller.py
Conté la lògica de negoci pel carretó:

- **`add_to_cart(product_id, quantity, session)`**: 
  - Valida que la quantitat sigui > 0 i ≤ 5
  - Comprova que no superi el límit total de 5 unitats per producte al carretó
  - Actualitza la sessió amb el carretó
  - Retorna (èxit, missatge)

- **`remove_from_cart(product_id, session)`**:
  - Elimina un producte del carretó
  - Retorna (èxit, missatge)

- **`validate_stock(product_id, quantity, db_path)`**:
  - Comprova que hi ha stock suficient
  - Retorna (vàlid, missatge_d'error)
  
- **`get_cart_total(cart, db_path)`**:
  - Calcula el total del carretó

**Regles implementades**:
✓ No superar 5 unitats per producte
✓ Validar stock abans d'afegir
✓ La quantitat ha de ser positiva

#### ✅ order_controller.py
Conté la lògica de negoci per les comandes:

- **`calculate_order_total(cart, db_path)`**:
  - Calcula el total sumant price * quantity per cada producte

- **`create_order(cart, username, password, email, db_path)`**:
  - Valida que el carretó no estigui buit
  - Valida el stock per a cada producte
  - Calcula el total
  - Crea o obté l'usuari
  - Crea la comanda (Order)
  - Crea els elements de la comanda (OrderItems)
  - Actualitza l'inventari (stock) de cada producte
  - Retorna l'ID de la comanda

**Responsabilitat**: Encapsula tota la lògica de creació de comandes, incloent transaccions i actualització d'inventari.

### 4. Routes (Capa de Presentació + Controladors)

✅ **app.py** - Aplicació Flask principal amb les següents rutes:

- **`/` (GET)**: 
  - Llista tots els productes
  - Crida a `Product.get_all()`
  - Renderitza `index.html`

- **`/add_to_cart` (POST)**:
  - Valida quantitat (1-5)
  - Crida `validate_stock()`
  - Comprova límit de 5 unitats al carretó
  - Crida `cart_controller.add_to_cart()`
  - Retorna redirect a `/cart` amb flash message

- **`/remove_from_cart` (POST)**:
  - Crida `cart_controller.remove_from_cart()`
  - Redirect a `/cart`

- **`/cart` (GET)**:
  - Obté productes del carretó de la sessió
  - Calcula totals
  - Renderitza `cart.html`

- **`/checkout` (GET/POST)**:
  - GET: mostra el formulari amb resum del carretó
  - POST: valida les dades del formulari
    - Nom d'usuari: 4-20 caràcters
    - Contrasenya: mínim 8 caràcters
    - Email: format vàlid
    - Adreça: com a mínim 10 caràcters
  - Crida `order_controller.create_order()`
  - Buida el carretó
  - Redirect amb flash message

**Responsabilitat**: Les rutes gestionen la comunicació HTTP i deleguen la lògica a les capes inferiors.

### 5. Templates (Vista)

✅ **base.html**: 
- Estructura base de totes les pàgines
- Navbar amb enllaços
- Sistema de flash messages
- Footer

✅ **index.html**: 
- Llista de productes en graella
- Formulari per afegir al carretó amb selector de quantitat (1-5)
- Botons "Afegir al Carretó" o "Sense Stock"
- Informació de stock visible

✅ **cart.html**: 
- Taula amb productes del carretó
- Subtotals i total
- Botons per eliminar productes
- Botó "Finalitzar Compra"
- Missatge si el carretó està buit

✅ **checkout.html**: 
- Resum de la compra
- Formulari de dades amb camps:
  - **username**: pattern="[A-Za-z0-9_]{4,20}", required, minlength=4, maxlength=20
  - **password**: required, minlength=8
  - **email**: type="email", pattern validat
  - **shipping_address**: required, minlength=10
- Validacions HTML5 i JavaScript addicionals
- Botons per confirmar o tornar enrere

### 6. Estils CSS

✅ **style.css**: 
- Disseny modern amb variables CSS
- Paleta de colors professional (blau primari)
- Layout responsiu amb Grid i Flexbox
- Cards amb sombres i transitions
- Flash messages amb colors diferents (success, error, info)
- Taules amb estil net
- Formularis amb focus states
- Botons amb estats hover
- Adaptat a mòbils (media queries)

### 7. JavaScript

✅ **main.js**:
- Validació de quantitats (1-5 unitats)
- Validació de formularis add_to_cart
- Auto-hide de flash messages després de 5 segons
- Funcions auxiliars per validació de camps
- Evita valors invàlids abans d'enviar

### 8. Configuració i Documentació

✅ **requirements.txt**: Flask i dependències
✅ **setup.sh**: Script d'instal·lació automàtica
✅ **.gitignore**: Exclusions adequades
✅ **README.md**: Documentació completa amb:
  - Descripció del projecte
  - Arquitectura explicada
  - Instruccions d'instal·lació
  - Funcionalitats implementades
  - Notes tècniques

## 🔄 Flux de dades (patró MVC)

```
Usuari → Browser → Flask Routes → Controllers → Models → Database
                                ↑                              ↓
                            Response ← Templates ← Controllers ←
```

1. **Browser**: L'usuari interactua amb la UI
2. **Routes**: Flask rep la petició i valida dades
3. **Controllers**: Processa la lògica de negoci (carretó, comanda)
4. **Models**: Accedeix a la base de dades
5. **Database**: SQLite emmagatzema les dades
6. **Response**: Flask retorna HTML renderitzat al browser

## ✅ Compliment de Requisits

### Requisits Funcionals

✓ **add_to_cart(product_id, quantity)**: Implementat amb validacions de quantitat i límit de 5 unitats
✓ **remove_from_cart(product_id)**: Implementat
✓ **validate_stock(product_id, quantity)**: Implementat
✓ **create_order(cart, user_id)**: Implementat amb càlcul de total i actualització d'inventari
✓ **show_products()**: Implementat amb ruta `/`
✓ **checkout()**: Implementat amb ruta GET i POST

### Validacions del Frontend

✓ Username: entre 4 i 20 caràcters (HTML5 pattern)
✓ Password: mínim 8 caràcters (HTML5 minlength)
✓ Email: format vàlid (HTML5 type="email" i pattern)
✓ Adreça: mínim 10 caràcters (HTML5 minlength)
✓ Quantitat: entre 1 i 5 (HTML5 type="number", min=1, max=5)
✓ JavaScript addicional per validacions en temps real

### Arquitectura MVC

✓ **Models**: models.py amb classes per cada entitat
✓ **Views**: templates/ amb plantilles HTML
✓ **Controllers**: controllers/ amb lògica de negoci

### Arquitectura en tres capes

✓ **Presentació**: HTML, CSS, JS
✓ **Lògica de Negoci**: cart_controller.py, order_controller.py
✓ **Dades**: models.py amb accés a SQLite

### Separació de responsabilitats

✓ No hi ha HTML amb SQL
✓ No hi ha lògica de negoci als templates
✓ Tots els accessos a DB a través de models
✓ Validacions tant al client com al servidor

### Ús de IA

✓ Documentat en AI-log.txt
✓ Regles establertes i respectades
✓ Codi generat amb guies apropiades
✓ Documentació completa

## 📊 Estructura Final del Projecte

```
5073-tech/
├── .gitignore
├── README.md                     # Documentació principal
├── IMPLEMENTACIÓ.md             # Aquest fitxer
├── requirements.txt              # Dependències
├── setup.sh                      # Script d'instal·lació
├── AI-log.txt                    # Historial d'ús de IA
└── back-end/
    ├── app.py                    # Aplicació Flask
    ├── models.py                 # Models de dades
    ├── controllers/
    │   ├── __init__.py
    │   ├── cart_controller.py    # Lògica del carretó
    │   └── order_controller.py  # Lògica de comandes
    ├── templates/
    │   ├── base.html             # Plantilla base
    │   ├── index.html            # Llista productes
    │   ├── cart.html             # Carretó
    │   └── checkout.html         # Finalització
    ├── static/
    │   ├── css/
    │   │   └── style.css         # Estils moderns
    │   └── js/
    │       └── main.js           # Validacions
    └── database/
        ├── db.sqlite3           # Base de dades
        ├── schema.sql           # Esquema
        ├── init_db.py           # Inicialització
        ├── erd.dot              # Diagrama ER
        └── README.md            # Docs BD
```

## 🎯 Resultat

L'aplicació està **completa** i **funcional**, seguint tots els requisits de la Pràctica TechShop:
- ✓ Patró MVC implementat
- ✓ Arquitectura en tres capes
- ✓ Separació de responsabilitats
- ✓ Validacions client i servidor
- ✓ Interfície moderna i responsiva
- ✓ Lògica de negoci encapsulada
- ✓ Base de dades funcional
- ✓ Documentació completa

