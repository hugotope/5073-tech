# TechShop - Aplicació Web de Comerç Electrònic

Aquesta és una aplicació web desenvolupada amb **Python + Flask** que implementa un sistema de gestió de productes i comandes per a **TechShop** (empresa fictícia de productes electrònics).

## 📋 Què fa l’aplicació

- Catàleg de productes amb **cerca** i **filtre per categories**
- **Carretó** (màxim **5** unitats per producte) amb validacions client + servidor
- **Checkout** amb dades d’enviament (incloent **ciutat / província / país** per anàlisi geogràfica)
- **Factura** després de la compra
- **Google Sheets** (opcional): export de recomanacions i export de la **compra** (línies de comanda)

## 🏗️ Arquitectura

L’aplicació segueix el patró **MVC** i separa responsabilitats:

```
5073-tech/
├── requirements.txt
├── README.md
├── setup.sh
└── back-end/
    ├── app.py                 # Flask: rutes i wiring
    ├── models.py              # Accés a dades (SQLite)
    ├── controllers/           # Casos d’ús / orquestració
    ├── services/              # Integracions (p.ex. Google Sheets)
    ├── templates/             # Vistes (Jinja2)
    ├── static/                # CSS/JS
    └── database/
        ├── db.sqlite3         # Dades locals (no versionar)
        ├── init_db.py
        ├── migrate_*.py
        ├── export_tableau_csv.py
        ├── export_analytics_tableau.py
        └── seed_orders_all_categories.py
```

## 🚀 Instal·lació i execució

### Prerequisits

- **Python 3.12+** (recomanat). També funciona amb Python 3.14, però en macOS/Homebrew sovint cal **venv** per instal·lar dependències (PEP 668).

### Opció A: `setup.sh` (venv a l’arrel)

```bash
chmod +x setup.sh
./setup.sh

source venv/bin/activate
cd back-end
python3 app.py
```

### Opció B: venv dins `back-end/` (recomanat si `pip` et diu “externally-managed-environment”)

```bash
cd back-end
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ../requirements.txt

python app.py
```

### Obrir l’app

Per defecte Flask arrenca a:

- `http://127.0.0.1:5001`

**Nota (macOS)**: si el **5000** està ocupat (p.ex. AirPlay Receiver), el projecte està configurat per usar **5001**.

## 🧩 Base de dades (SQLite)

Inicialització:

```bash
cd back-end/database
python3 init_db.py
```

Si la BD no existeix, `app.py` també pot intentar inicialitzar-la en desenvolupament, però és millor executar `init_db.py` explícitament.

## 📊 Tableau (export de dades)

Els scripts generen fitxers a `back-end/database/`:

- `python3 export_tableau_csv.py` → `techshop_todo_tableau.csv` + `.tsv`
- `python3 export_analytics_tableau.py` → `techshop_vendes_analytics.csv` + `.tsv`

Recomanació per Tableau Desktop (locale CA/ES): **`*.tsv`** (tabulador) sol inferir millor els tipus numèrics.

## 📈 Google Sheets (opcional)

### 1) Credencials (Service Account)

1. Crea un **Service Account** a Google Cloud i genera un JSON de clau.
2. Comparteix el Google Sheet amb el **client_email** del service account (permís **Editor**).
3. Crea un fitxer `.env` a l’**arrel del repo** (`5073-tech/.env`) amb:

```bash
GOOGLE_APPLICATION_CREDENTIALS=back-end/tech-xxxx.json
TECHSHOP_SPREADSHEET_ID=<id_del_document>
# Opcional (per defecte: Comandes)
TECHSHOP_ORDER_SHEET_NAME=Comandes
```

**Important**

- **No commitis** `.env` ni el JSON de credencials (ja estan ignorats al `.gitignore`).
- El codi resol `GOOGLE_APPLICATION_CREDENTIALS` de forma robusta tant si executes Flask des de `back-end/` com des de l’arrel.

### 2) Què pots exportar des de la web

- **Recomanacions + stock**: botó a la home (quan Sheets està configurat).
- **Compra (línies de comanda)**: botó a la **factura** després de comprar (escriu a la pestanya **`Comandes`** del mateix spreadsheet, sense esborrar la fulla de recomanacions).

### 3) Provar des de terminal

```bash
cd /ruta/al/repositori/5073-tech
source back-end/.venv/bin/activate  # o: source venv/bin/activate
python back-end/scripts/sync_sheets.py
```

## ✨ Funcionalitats principals (resum tècnic)

- Validació de **stock** i límit de **5** unitats / producte al carretó
- Checkout amb **adreça** i **ubicació** (ciutat/província/país)
- Integració **Google Sheets** via `gspread` + `google-auth`

## 🔒 Seguretat (acadèmia / dev)

- `app.secret_key` és un placeholder: **canvia’l** si desplegues en serio.
- Les contrasenyes del projecte són un hash simple (SHA-256) pensat per pràctica: en producció cal **bcrypt/argon2**.

## 🤖 Ús d’IA

Durant el desenvolupament s’ha fet servir IA per esbossos, revisió i documentació. El procés queda reflectit a `AI-log.txt` (si existeix al teu entorn).

## 👨‍💻 Autor

Pràctica 5073 — TechShop (Flask + SQLite + integracions).

## 📄 Llicència

Projecte acadèmic; no està pensat per a producció.
