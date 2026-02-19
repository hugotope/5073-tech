"""Migració per al dataset Tableau Story (TechShop).

Afegeix:
- Taula Subcategory i subcategory_id a Product (Categoria → Subcategoria → Producte).
- Columna segment a UserAccount (perfil d'usuari).
- Columnes shipping_city, shipping_province, shipping_country a Order (anàlisi geogràfica).

Després sembra subcategories, assigna subcategoria als productes, assigna segment als usuaris
i omple les comandes amb ubicacions (per poder fer mapes a Tableau).

Executa des de back-end/database:
  python migrate_tableau_dataset.py
"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"

# Subcategories per category_id: (category_id, name, slug)
SUBCATEGORIES = [
    (1, "Raspberry Pi", "raspberry-pi"),
    (1, "Arduino", "arduino"),
    (1, "ESP / NodeMCU", "esp-nodemcu"),
    (1, "Altres plaques", "altres-plaques"),
    (2, "Temperatura i humitat", "temperatura-humitat"),
    (2, "Distància i proximitat", "distancia-proximitat"),
    (2, "Moviment i so", "moviment-so"),
    (2, "Ambient i especial", "ambient-especial"),
    (3, "LED individuals", "led-individuals"),
    (3, "Tires i panells", "tires-panells"),
    (3, "Kits i drivers", "kits-drivers"),
    (4, "Resistències i condensadors", "resistencies-condensadors"),
    (4, "Breadboard i cables", "breadboard-cables"),
    (4, "Semiconductors i alimentació", "semiconductors-alimentacio"),
    (5, "LCD i OLED", "lcd-oled"),
    (5, "TFT i tàctil", "tft-tactil"),
    (5, "7 segments i matrius", "7seg-matrius"),
    (6, "Comunicació", "comunicacio"),
    (6, "Alimentació i relé", "alimentacio-rele"),
    (6, "Altres mòduls", "altres-moduls"),
    (7, "Servos", "servos"),
    (7, "Motors DC i step", "motors-dc-step"),
    (7, "Drivers i kits", "drivers-kits"),
    (8, "Monitors estàndard", "monitors-estandard"),
    (8, "Monitors gaming i professional", "monitors-gaming-pro"),
]

# product_id -> subcategory_id (ordre dels 100 productes del seed)
# Plaques 1-14: 1-5=Raspberry(1), 6-8=Arduino(2), 9-11=ESP(3), 12-14=Altres(4)
# Sensors 15-28: 15-16=Temperatura(5), 17-20=Distància(6), 21-24=Moviment(7), 25-28=Ambient(8)
# LED 29-40: 29-30=individuals(9), 31-34=tires(10), 35-40=kits(11)
# Components 41-58: 41-44=Resistències(12), 45-48=Breadboard(13), 49-58=Semiconductors(14)
# Displays 59-70: 59-62=LCD(15), 63-66=TFT(16), 67-70=7seg(17)
# Mòduls 71-84: 71-76=Comunicació(18), 77-80=Alimentació(19), 81-84=Altres(20)
# Motors 85-94: 85-86=Servos(21), 87-92=Motors DC/step(22), 93-94=Drivers(23)
# Monitors 95-102: 95-98=estàndard(24), 99-102=gaming/pro(25)
PRODUCT_SUBCATEGORY = [
    1, 1, 1, 1, 1,  2, 2, 2,  3, 3, 3,  4, 4, 4,   # 1-14 Plaques
    5, 5,  6, 6, 6, 6,  7, 7, 7, 7,  8, 8, 8, 8,   # 15-28 Sensors
    9, 9,  10, 10, 10, 10, 10, 10,  11, 11, 11, 11,  # 29-40 LED
    12, 12, 12, 12,  13, 13, 13, 13,  14, 14, 14, 14, 14, 14, 14, 14, 14, 14,  # 41-58 Components
    15, 15, 15, 15,  16, 16, 16, 16,  17, 17, 17, 17,  # 59-70 Displays
    18, 18, 18, 18, 18, 18,  19, 19, 19, 19,  20, 20, 20, 20,  # 71-84 Mòduls
    21, 21,  22, 22, 22, 22, 22, 22,  23, 23,  # 85-94 Motors
    24, 24, 24, 24,  25, 25, 25, 25,  # 95-102 Monitors
]

# Ubicacions per província/país (per omplir comandes)
LOCATIONS = [
    ("Barcelona", "Barcelona", "Espanya"),
    ("L'Hospitalet", "Barcelona", "Espanya"),
    ("Badalona", "Barcelona", "Espanya"),
    ("Girona", "Girona", "Espanya"),
    ("Figueres", "Girona", "Espanya"),
    ("Lleida", "Lleida", "Espanya"),
    ("Tarragona", "Tarragona", "Espanya"),
    ("Reus", "Tarragona", "Espanya"),
    ("Madrid", "Madrid", "Espanya"),
    ("València", "València", "Espanya"),
    ("Sevilla", "Sevilla", "Espanya"),
    ("Bilbao", "Biscaia", "Espanya"),
    ("Zaragoza", "Zaragoza", "Espanya"),
]

# Segments d'usuari per anàlisi per perfil
SEGMENTS = ["Professional", "Aficionat", "Educació", "Professional", "Aficionat", "Educació"]


def migrate():
    if not DB_PATH.exists():
        print("No s'ha trobat db.sqlite3. Executa init_db.py primer.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # --- Subcategory ---
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Subcategory'"
        )
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE Subcategory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(80) NOT NULL,
                    slug VARCHAR(80) NOT NULL,
                    category_id INTEGER NOT NULL,
                    FOREIGN KEY(category_id) REFERENCES Category(id)
                )
            """)
            print("Taula Subcategory creada.")
        n_sub = cur.execute("SELECT COUNT(*) FROM Subcategory").fetchone()[0]
        if n_sub == 0:
            cur.executemany(
                "INSERT INTO Subcategory(name, slug, category_id) VALUES(?,?,?)",
                [(n, s, cid) for cid, n, s in SUBCATEGORIES],
            )
            print("Subcategories inserides.")
        else:
            print("Subcategory ja té dades.")

        # --- Product.subcategory_id ---
        cur.execute("PRAGMA table_info(Product)")
        cols = [row[1] for row in cur.fetchall()]
        if "subcategory_id" not in cols:
            cur.execute("ALTER TABLE Product ADD COLUMN subcategory_id INTEGER REFERENCES Subcategory(id)")
            for pid, subid in enumerate(PRODUCT_SUBCATEGORY, start=1):
                cur.execute(
                    "UPDATE Product SET subcategory_id = ? WHERE id = ?",
                    (subid, pid),
                )
            # Asignar subcategoria 1 als productes que no tinguin (per si n'hi ha més de 102)
            cur.execute(
                "UPDATE Product SET subcategory_id = 1 WHERE subcategory_id IS NULL"
            )
            print("Columna Product.subcategory_id afegida i assignada.")
        else:
            print("Product.subcategory_id ja existeix.")

        # --- UserAccount.segment ---
        cur.execute("PRAGMA table_info(UserAccount)")
        cols = [row[1] for row in cur.fetchall()]
        if "segment" not in cols:
            cur.execute(
                "ALTER TABLE UserAccount ADD COLUMN segment VARCHAR(50) DEFAULT 'Aficionat'"
            )
            users = cur.execute("SELECT id FROM UserAccount ORDER BY id").fetchall()
            for i, (uid,) in enumerate(users):
                seg = SEGMENTS[i % len(SEGMENTS)]
                cur.execute(
                    "UPDATE UserAccount SET segment = ? WHERE id = ?", (seg, uid)
                )
            print("Columna UserAccount.segment afegida i assignada.")
        else:
            print("UserAccount.segment ja existeix.")

        # --- Order: shipping_city, shipping_province, shipping_country ---
        cur.execute("PRAGMA table_info(\"Order\")")
        cols = [row[1] for row in cur.fetchall()]
        for col in ("shipping_city", "shipping_province", "shipping_country"):
            if col not in cols:
                cur.execute(
                    f'ALTER TABLE "Order" ADD COLUMN {col} VARCHAR(100)'
                )
        # Omplir comandes existents sense ubicació
        orders = cur.execute(
            'SELECT id FROM "Order" WHERE shipping_city IS NULL OR shipping_city = "" ORDER BY id'
        ).fetchall()
        for i, (oid,) in enumerate(orders):
            city, prov, country = LOCATIONS[i % len(LOCATIONS)]
            cur.execute(
                """UPDATE "Order" SET shipping_city = ?, shipping_province = ?, shipping_country = ?
                   WHERE id = ?""",
                (city, prov, country, oid),
            )
        if orders:
            print(f"Order: ubicacions assignades a {len(orders)} comandes.")
        else:
            print("Order: sense comandes pendents d’ubicació.")

        conn.commit()
        print("Migració Tableau dataset completada.")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
