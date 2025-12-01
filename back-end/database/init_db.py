"""Inicialitza la base de dades SQLite per a la pràctica TechShop.

Crearà un fitxer `db.sqlite3` a la mateixa carpeta, executarà `schema.sql` i
insertarà dades d'exemple.
"""
import sqlite3
import pathlib
import csv
import secrets

from werkzeug.security import generate_password_hash

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
        
        # Inserir productes d'exemple (més productes per a recomanacions)
        products = [
            ("Raspberry Pi 4 Model B", 55.00, 10),
            ("Arduino Uno Rev3", 22.50, 25),
            ("Sensor DHT22", 8.90, 50),
            ("ESP32 Development Board", 12.99, 30),
            ("Sensor Ultrasonic HC-SR04", 3.50, 40),
            ("LED RGB 5mm", 0.50, 100),
            ("Resistència Pack 220Ω", 2.99, 80),
            ("Breadboard 830 punts", 5.99, 35),
            ("Cable jumper pack", 4.50, 45),
            ("Motor Servo SG90", 6.99, 20),
            ("Display LCD 16x2", 8.50, 25),
            ("Mòdul Bluetooth HC-05", 9.99, 15),
        ]
        cur.executemany("INSERT INTO Product(name, price, stock) VALUES(?,?,?)", products)

        # Inserir usuaris d'exemple amb diferents patrons de compra
        users_data = [
            ("alumn01", "password123", "alumn01@example.com"),
            ("maria_tech", "password123", "maria@example.com"),
            ("joan_dev", "password123", "joan@example.com"),
            ("anna_iot", "password123", "anna@example.com"),
            ("carlos_arduino", "password123", "carlos@example.com"),
            ("laura_rasp", "password123", "laura@example.com"),
        ]
        
        user_ids = []
        for username, password, email in users_data:
            # Utilitzem el mateix mecanisme segur que en producció (PBKDF2 + salt pròpia)
            salt = secrets.token_hex(16)
            password_input = f"{salt}{password}"
            password_hash = generate_password_hash(
                password_input, method="pbkdf2:sha256", salt_length=16
            )
            cur.execute(
                "INSERT INTO UserAccount(username, password_hash, salt, email) "
                "VALUES(?,?,?,?)",
                (username, password_hash, salt, email),
            )
            user_ids.append(cur.lastrowid)

        # Crear comandes amb patrons de compra similars per a recomanacions
        # Usuari 1 (alumn01): Raspberry Pi, Arduino, Sensor DHT22
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (86.40, user_ids[0]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 1, 1))  # Raspberry Pi
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 2, 1))  # Arduino
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 3, 1))  # DHT22

        # Usuari 2 (maria_tech): Arduino, Sensor DHT22, ESP32 (similar a usuari 1)
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (44.39, user_ids[1]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 2, 1))  # Arduino
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 3, 2))  # DHT22
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 4, 1))  # ESP32

        # Usuari 3 (joan_dev): Raspberry Pi, ESP32, Breadboard (similar a usuari 1)
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (73.98, user_ids[2]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 1, 1))  # Raspberry Pi
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 4, 1))  # ESP32
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 8, 1))  # Breadboard

        # Usuari 4 (anna_iot): Arduino, Sensor Ultrasonic, LED RGB, Servo
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (33.98, user_ids[3]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 2, 1))  # Arduino
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 5, 2))  # Ultrasonic
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 6, 10))  # LED RGB
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 10, 1))  # Servo

        # Usuari 5 (carlos_arduino): Arduino, Sensor Ultrasonic, Breadboard, Cable jumper
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (36.98, user_ids[4]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 2, 1))  # Arduino
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 5, 1))  # Ultrasonic
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 8, 1))  # Breadboard
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 9, 1))  # Cable jumper

        # Usuari 6 (laura_rasp): Raspberry Pi, Display LCD, Bluetooth
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (73.99, user_ids[5]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 1, 1))  # Raspberry Pi
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 11, 1))  # Display LCD
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 12, 1))  # Bluetooth

        # Segona comanda per usuari 2 (maria_tech): Breadboard, Cable jumper (productes que altres usuaris similars han comprat)
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (10.49, user_ids[1]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 8, 1))  # Breadboard
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 9, 1))  # Cable jumper

        # Segona comanda per usuari 3 (joan_dev): Sensor DHT22, Cable jumper
        cur.execute("INSERT INTO \"Order\"(total, user_id) VALUES(?,?)", (13.40, user_ids[2]))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 3, 1))  # DHT22
        cur.execute("INSERT INTO OrderItem(order_id, product_id, quantity) VALUES(?,?,?)", (order_id, 9, 1))  # Cable jumper

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
