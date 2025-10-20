"""Inicialitza la base de dades SQLite per a la pràctica TechShop.

Crearà un fitxer `db.sqlite3` a la mateixa carpeta, executarà `schema.sql` i
insertarà dades d'exemple.
"""
import sqlite3
import pathlib
import csv

HERE = pathlib.Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"
SCHEMA_PATH = HERE / "schema.sql"

def init_db():
    print(f"Inicialitzant la base de dades a: {DB_PATH}")
    # Si ja existeix, l'eliminem per recrear una base neta (facilita reexecució durant la pràctica)
    if DB_PATH.exists():
        print("S'ha detectat una base de dades ja existent. S'eliminarà per recrear-la.")
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        schema = SCHEMA_PATH.read_text(encoding='utf-8')
        conn.executescript(schema)
        print("Esquema aplicat.")

        cur = conn.cursor()
        # Inserir alguns productes d'exemple
        products = [
            ("Raspberry Pi 4 Model B", 55.00, 10),
            ("Arduino Uno Rev3", 22.50, 25),
            ("Sensor DHT22", 8.90, 50),
        ]
        cur.executemany("INSERT INTO Product(name, price, stock) VALUES(?,?,?)", products)

        # Inserir un usuari d'exemple (password hash fictici — per a la pràctica no cal generar un hash real)
        cur.execute("INSERT INTO UserAccount(username, password_hash, email) VALUES(?,?,?)",
                    ("alumn01", "$2b$12$examplehashvalue..................", "alumn01@example.com"))
        user_id = cur.lastrowid

        # Crear una comanda d'exemple
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (86.4, user_id))
        order_id = cur.lastrowid

        # Afegir items a la comanda
        # Assumim product_id 1 i 2 existeixen
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 1, 1))
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 2, 3))

        conn.commit()
        print("Dades d'exemple inserides.")

        # Mostrar resum de taules existents i comptatges
        print('\nTaules presents i nombre de registres:')
        for table_row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            table_name = table_row[0]
            count = cur.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
            print(f" - {table_name}: {count} registres")

    print("Hecho.")


if __name__ == '__main__':
    init_db()
