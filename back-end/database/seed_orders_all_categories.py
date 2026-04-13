"""Afegeix moltes comandes amb productes de TOTES les categories per que els gràfics Tableau tinguin més informació.

- Més comandes i més línies per comanda
- Productes de les 8 categories: Plaques, Sensors, LED, Components, Displays, Mòduls, Motors, Monitors
- Tots els usuaris (1-6) i totes les ubicacions
- Després d’executar, torna a generar l’export: python3 export_tableau_csv.py

Executa des de back-end/database (després de init_db.py i migrate_tableau_dataset.py):
  python3 seed_orders_all_categories.py
"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"

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

# (user_id 1-6, [(product_id, quantity), ...], location_index)
# Productes: 1-14 Plaques, 15-28 Sensors, 29-40 LED, 41-58 Components, 59-70 Displays, 71-84 Mòduls, 85-94 Motors, 95-102 Monitors
ORDERS_TO_ADD = [
    (1, [(15, 2), (29, 5), (41, 1)], 0),      # Sensors + LED + Components
    (2, [(59, 1), (71, 2)], 1),              # Displays + Mòduls
    (3, [(85, 2), (41, 2)], 2),              # Motors + Components
    (4, [(95, 1)], 3),                        # Monitors
    (5, [(17, 1), (31, 1), (45, 1)], 4),     # Sensors + LED + Components
    (6, [(72, 1), (86, 1), (59, 1)], 0),     # Mòduls + Motors + Displays
    (1, [(22, 2), (33, 1)], 1),              # Sensors + LED
    (2, [(96, 1), (42, 3)], 2),              # Monitors + Components
    (3, [(1, 1), (16, 2), (30, 10)], 5),     # Plaques + Sensors + LED
    (4, [(60, 1), (73, 1), (44, 2)], 6),     # Displays + Mòduls + Components
    (5, [(87, 2), (46, 1)], 7),              # Motors + Components
    (6, [(18, 1), (34, 2)], 8),              # Sensors + LED
    (1, [(97, 1)], 9),                        # Monitors
    (2, [(2, 1), (19, 2), (35, 5)], 10),     # Plaques + Sensors + LED
    (3, [(61, 2), (74, 1)], 11),             # Displays + Mòduls
    (4, [(88, 1), (47, 2)], 12),             # Motors + Components
    (5, [(20, 1), (36, 3), (48, 1)], 0),     # Sensors + LED + Components
    (6, [(98, 1), (62, 1)], 1),              # Monitors + Displays
    (1, [(3, 1), (21, 2)], 2),               # Plaques + Sensors
    (2, [(75, 2), (89, 1)], 3),             # Mòduls + Motors
    (3, [(37, 4), (49, 1)], 4),              # LED + Components
    (4, [(63, 1), (99, 1)], 5),              # Displays + Monitors
    (5, [(4, 1), (23, 1), (38, 2)], 6),      # Plaques + Sensors + LED
    (6, [(76, 1), (90, 2)], 7),              # Mòduls + Motors
    (1, [(50, 2), (64, 1)], 8),              # Components + Displays
    (2, [(24, 1), (39, 5)], 9),              # Sensors + LED
    (3, [(100, 1), (77, 1)], 10),            # Monitors + Mòduls
    (4, [(5, 2), (25, 2)], 11),              # Plaques + Sensors
    (5, [(91, 1), (51, 1)], 12),             # Motors + Components
    (6, [(40, 3), (65, 1)], 0),              # LED + Displays
    (1, [(6, 1), (26, 1), (78, 2)], 1),      # Plaques + Sensors + Mòduls
    (2, [(92, 1), (52, 2)], 2),              # Motors + Components
    (3, [(66, 1), (101, 1)], 3),             # Displays + Monitors
    (4, [(27, 2), (79, 1)], 4),              # Sensors + Mòduls
    (5, [(7, 1), (53, 1)], 5),               # Plaques + Components
    (6, [(93, 2), (67, 1)], 6),              # Motors + Displays
    (1, [(28, 1), (80, 1)], 7),              # Sensors + Mòduls
    (2, [(8, 1), (54, 2)], 8),               # Plaques + Components
    (3, [(68, 1), (102, 1)], 9),            # Displays + Monitors
    (4, [(9, 2), (81, 1)], 10),              # Plaques + Mòduls
    (5, [(94, 1), (55, 1)], 11),             # Motors + Components
    (6, [(69, 1), (82, 2)], 12),             # Displays + Mòduls
    (1, [(10, 1), (56, 2)], 0),              # Plaques + Components
    (2, [(70, 1), (83, 1)], 1),              # Displays + Mòduls
    (3, [(11, 1), (57, 1)], 2),              # Plaques + Components
    (4, [(84, 2), (58, 1)], 3),              # Mòduls + Components
    (5, [(12, 1), (14, 1)], 4),              # Plaques
    (6, [(13, 2), (15, 1)], 5),               # Plaques + Sensors
]


def main():
    if not DB_PATH.exists():
        print("No s'ha trobat db.sqlite3. Executa init_db.py i migrate_tableau_dataset.py.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('PRAGMA table_info("Order")')
    cols = [r[1] for r in cur.fetchall()]
    if "shipping_city" not in cols:
        print("Executa abans: python3 migrate_tableau_dataset.py")
        conn.close()
        return

    for user_id_1based, items, loc_idx in ORDERS_TO_ADD:
        city, prov, country = LOCATIONS[loc_idx % len(LOCATIONS)]
        total = 0.0
        for pid, qty in items:
            row = cur.execute("SELECT price FROM Product WHERE id = ?", (pid,)).fetchone()
            if row:
                total += row[0] * qty
        total = round(total, 2)
        cur.execute(
            """INSERT INTO "Order" (total, user_id, shipping_city, shipping_province, shipping_country)
               VALUES (?, ?, ?, ?, ?)""",
            (total, user_id_1based, city, prov, country),
        )
        order_id = cur.lastrowid
        for pid, qty in items:
            cur.execute(
                "INSERT INTO OrderItem (order_id, product_id, quantity) VALUES (?, ?, ?)",
                (order_id, pid, qty),
            )

    conn.commit()
    n_orders = len(ORDERS_TO_ADD)
    n_lines = sum(len(items) for _, items, _ in ORDERS_TO_ADD)
    conn.close()
    print(f"Afegides {n_orders} comandes ({n_lines} línies) amb productes de totes les categories.")
    print("Torna a executar: python3 export_tableau_csv.py")


if __name__ == "__main__":
    main()
