"""Migració: afegir taula Category i category_id a Product.

Executa aquest script si ja tens una base de dades sense categories:
  cd back-end/database && python migrate_add_categories.py
"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"


def migrate():
    if not DB_PATH.exists():
        print("No s'ha trobat db.sqlite3. Executa init_db.py primer.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # Comprovar si ja existeix la taula Category
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Category'"
        )
        if cur.fetchone():
            print("La taula Category ja existeix. Res a fer.")
            return
        # Crear taula Category
        cur.execute("""
            CREATE TABLE Category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                slug VARCHAR(50) NOT NULL UNIQUE
            )
        """)
        # Inserir categories per defecte
        categories = [
            ("Plaques", "plaques"),
            ("Sensors", "sensors"),
            ("LED", "led"),
            ("Components", "components"),
            ("Displays", "displays"),
            ("Mòduls", "moduls"),
            ("Motors i Servos", "motors-servos"),
            ("Monitors", "monitors"),
        ]
        cur.executemany(
            "INSERT INTO Category(name, slug) VALUES(?,?)", categories
        )
        # Afegir columna category_id a Product si no existeix
        cur.execute("PRAGMA table_info(Product)")
        columns = [row[1] for row in cur.fetchall()]
        if "category_id" not in columns:
            cur.execute("ALTER TABLE Product ADD COLUMN category_id INTEGER DEFAULT 1")
            # Assignar categories per product_id (ordre de init_db: 1=Raspberry, 2=Arduino, ...)
            # 1=Plaques, 2=Sensors, 3=LED, 4=Components, 5=Displays, 6=Mòduls, 7=Motors
            product_category = [
                (1, 1), (2, 1), (3, 2), (4, 1), (5, 2), (6, 3), (7, 4), (8, 4),
                (9, 4), (10, 7), (11, 5), (12, 6),
            ]
            for product_id, cat_id in product_category:
                cur.execute(
                    "UPDATE Product SET category_id = ? WHERE id = ?",
                    (cat_id, product_id),
                )
            cur.execute("UPDATE Product SET category_id = 1 WHERE category_id IS NULL OR category_id = 0")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_product_category ON Product(category_id)")
        conn.commit()
        print("Migració aplicada: taula Category creada i productes assignats.")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
