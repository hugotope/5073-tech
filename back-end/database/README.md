# TechShop - Base de dades (SQLite)

Aquest directori conté els fitxers necessaris per crear i inicialitzar la base de dades SQLite utilitzada en la pràctica.

Fitxers principals:

- `schema.sql`: Esquema de la base de dades amb les taules `Product`, `UserAccount`, `Order` i `OrderItem`.
- `init_db.py`: Script Python que crea `db.sqlite3`, aplica l'esquema i insereix dades d'exemple.
- `erd.dot`: Diagrama entitat-relació en format Graphviz DOT.

Entitats i camps (resum):

- Product
  - id: INTEGER, PK, autoincremental
  - name: VARCHAR(100)
  - price: DECIMAL(10,2)
  - stock: INTEGER

- UserAccount
  - id: INTEGER, PK, autoincremental
  - username: VARCHAR(20) (4-20 caràcters)
  - password_hash: VARCHAR(60) (no emmagatzemar contrasenyes en text pla)
  - email: VARCHAR(100)
  - created_at: DATETIME

- Order
  - id: INTEGER, PK, autoincremental
  - total: DECIMAL(10,2)
  - created_at: DATETIME
  - user_id: INTEGER, FK -> UserAccount(id)

- OrderItem
  - id: INTEGER, PK, autoincremental
  - order_id: INTEGER, FK -> Order(id)
  - product_id: INTEGER, FK -> Product(id)
  - quantity: INTEGER

Relacions:

- Un `UserAccount` pot tenir moltes `Order`.
- Cada `Order` pot tenir moltes `OrderItem`.
- Cada `OrderItem` referencia un sol `Product`.

Com executar

1. Assegura't de tenir Python 3 instal·lat.
2. Obre una terminal i navega a aquest directori:

```powershell
cd C:\Users\D3T\VS\5073-tech\back-end\database
```

3. Executa l'script d'inicialització:

```powershell
python .\init_db.py
```

Després d'executar-ho, es crearà el fitxer `db.sqlite3` amb l'esquema i dades d'exemple.

Generar el diagrama visual

Si tens Graphviz instal·lat, pots generar un PNG amb:

```powershell
dot -Tpng erd.dot -o erd.png
```

Notes de seguretat i millores possibles

- Emmagatzemar `password_hash` hauria de fer-se amb un algorisme robust (bcrypt/argon2). En l'exemple s'ha deixat un valor fictici.
- Afegir gestió d'estat d'ordres (pendent, enviat, cancel·lat) podria ser útil.
- Considerar auditories o triggers per controlar canvis d'inventari.
