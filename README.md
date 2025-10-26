# TechShop - Aplicació Web de Comerç Electrònic

Aquesta és una aplicació web desenvolupada amb Python i Flask que implementa un sistema de gestió de productes i comandes per a TechShop, una empresa fictícia de productes electrònics.

## 📋 Descripció del Projecte

TechShop és una aplicació web que permet als usuaris:
- Veure productes disponibles
- Afegir productes al carretó de compres (màxim 5 unitats per producte)
- Gestionar el carretó
- Finalitzar compres amb validació de dades

L'aplicació segueix el **patró Model-Vista-Controlador (MVC)** i l'**arquitectura en tres capes**:

- **Capa de Presentació**: Plantilles HTML, CSS i JavaScript
- **Capa de Lògica de Negoci**: Funcions de servei (services/controllers)
- **Capa de Dades**: Models i accés a la base de dades SQLite

## 🏗️ Arquitectura

```
5073-tech/
├── back-end/
│   ├── app.py                 # Aplicació Flask principal
│   ├── models.py              # Models de dades (Product, Order, etc.)
│   ├── controllers/           # Lògica de negoci
│   │   ├── cart_controller.py    # Gestió del carretó
│   │   └── order_controller.py   # Gestió de comandes
│   ├── templates/             # Plantilles HTML
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── cart.html
│   │   └── checkout.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Estils moderns i responsius
│   │   └── js/
│   │       └── main.js         # Validacions del client
│   └── database/
│       ├── db.sqlite3         # Base de dades SQLite
│       ├── schema.sql         # Esquema de la base de dades
│       ├── init_db.py         # Script d'inicialització
│       ├── erd.dot            # Diagrama entitat-relació
│       └── README.md
├── requirements.txt           # Dependències Python
└── README.md                  # Aquest fitxer
```

## 🚀 Instal·lació i Execució

### Prerequisits

- Python 3.8 o superior
- pip (gestor de paquets de Python)

### Passos per instal·lar

#### Opció 1: Script automàtic (recomanat)

```bash
# Donar permisos d'execució (si cal)
chmod +x setup.sh

# Executar el script d'instal·lació
./setup.sh

# Activar l'entorn virtual i executar
source venv/bin/activate
cd back-end
python3 app.py
```

#### Opció 2: Manual

1. **Creeu un entorn virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. **Instal·leu les dependències**
```bash
pip install -r requirements.txt
```

3. **Inicialitzeu la base de dades**
```bash
cd back-end/database
python3 init_db.py
cd ../..
```

4. **Executeu l'aplicació**
```bash
cd back-end
python3 app.py
```

5. **Obriu el navegador**
Accediu a: `http://localhost:5001`

**Nota**: Si el port 5000 està en ús (per AirPlay Receiver en macOS), l'aplicació s'executarà al port 5001.

## ✨ Funcionalitats Implementades

### Funcions de Lògica de Negoci

- **`add_to_cart(product_id, quantity)`**: Afegeix un producte al carretó amb validacions:
  - Comprova que la quantitat sigui un enter positiu
  - No supera el límit de 5 unitats del mateix producte al carretó
  - Valida que hi ha stock disponible

- **`remove_from_cart(product_id)`**: Elimina un producte del carretó

- **`validate_stock(product_id, quantity)`**: Comprova que hi ha stock suficient abans d'afegir al carretó

- **`create_order(cart, user_id)`**: Crea una comanda:
  - Calcula el total de la comanda
  - Crea o obté l'usuari
  - Crea la comanda i els seus elements
  - Actualitza l'inventari restant les unitats comprades

### Validacions del Frontend

#### Client (HTML5 + JavaScript)
- Nom d'usuari: entre 4 i 20 caràcters (pattern: `[A-Za-z0-9_]{4,20}`)
- Contrasenya: mínim 8 caràcters
- Email: format vàlid
- Adreça d'enviament: mínim 10 caràcters
- Quantitat de productes: entre 1 i 5 unitats (input type='number' amb min=1, max=5)

#### Servidor (Python/Flask)
- Totes les validacions del client es re-validen al servidor
- Error handling robust
- Missatges d'error clars per a l'usuari

## 🗄️ Base de Dades

### Esquema

La base de dades SQLite conté 4 taules principals:

- **Product**: Productes disponibles (id, name, price, stock)
- **UserAccount**: Comptes d'usuari (id, username, password_hash, email, created_at)
- **Order**: Comandes (id, total, created_at, user_id)
- **OrderItem**: Elements de les comandes (id, order_id, product_id, quantity)

### Relacions

- Un `UserAccount` pot tenir moltes `Order`
- Cada `Order` pot tenir molts `OrderItem`
- Cada `OrderItem` referencia un sol `Product`

## 🎨 Característiques de Disseny

- **UI Moderna**: Disseny net i professional amb CSS modern
- **Responsive**: Adaptat a dispositius mòbils i tablet
- **Accessible**: Utilitza atributs HTML adequats per a l'accessibilitat
- **UX Millorada**: Missatges flash, validacions en temps real, feedback visual

## 🔒 Seguretat i Validacions

### Regles Implementades

1. **No barregar codi HTML amb consultes SQL o lògica de negoci**
   - Tota la lògica de negocis està separada en controllers/
   - Els models gestionen tot l'accés a la base de dades

2. **Tots els accessos a la base de dades a través de funcions específiques**
   - Cada entitat té les seves funcions de model
   - No hi ha SQL directe en els templates o rutes

3. **No superar les 5 unitats per producte al carretó**
   - Validació tant al client com al servidor
   - Missatges d'error clars

4. **Validar sempre les dades rebudes des del client**
   - Validacions HTML5 al client
   - Re-validació al servidor
   - Sanitització de dades

## 🤖 Ús de Intel·ligència Artificial

Durant el desenvolupament d'aquest projecte s'ha fet servir IA (GitHub Copilot/Claude) per a:

1. **Generació d'esbossos de codi**: Estructura inicial de classes i funcions
2. **Revisió de codi**: Verificació de respecte de l'arquitectura MVC
3. **Suggeriments d'optimització**: Millora de la gestió del carretó i validacions
4. **Documentació**: Generació de docstrings i comentaris

Tot el procés està documentat al fitxer `AI-log.txt`.

### Regles establertes per a la IA

- No barregar codi HTML amb consultes SQL o lògica de negoci
- Tots els accessos a la base de dades s'han de fer a través de funcions específiques en la capa de models
- No superar les 5 unitats per producte al carretó
- Validar sempre les dades rebudes des del client abans de processar-les

## 📝 Notes Tècniques

### Canvis respecte a l'esquema original

- La taula `User` s'ha renomenat a `UserAccount` per evitar conflictes amb la paraula reservada `USER` en alguns RDBMS

### Millores futures possibles

- Utilitzar bcrypt/argon2 per a generació de password hash
- Afegir camp d'estat en `Order` (pending/shipped/cancelled)
- Afegir triggers o procediments per decrementar `Product.stock` automàticament
- Implementar autenticació de sessions més robusta
- Afegir tests unitaris

## 👨‍💻 Autor

Pràctica realitzada per a l'assignatura 5073, aplicant el patró MVC i l'arquitectura en tres capes amb Flask.

## 📄 Llicència

Aquest projecte és una pràctica acadèmica i no està destinat a producció.

