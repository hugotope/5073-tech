#!/usr/bin/env python3
"""Exporta dades de vendes TechShop per Tableau (Story).

Genera dos fitxers:
- techshop_vendes_para_tableau.csv (delimitador ;)
- techshop_vendes_para_tableau.tsv (delimitador Tab) — recomanat per Tableau

Ús: cd back-end/database && python3 export_tableau_csv.py
"""
import csv
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"
OUT_CSV = HERE / "techshop_vendes_para_tableau.csv"
OUT_TSV = HERE / "techshop_vendes_para_tableau.tsv"

def main():
    if not DB_PATH.exists():
        print(f"No s'ha trobat {DB_PATH}. Executa init_db.py i migrate_tableau_dataset.py.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    SELECT
        o.id AS order_id,
        o.created_at AS order_date,
        o.total AS order_total,
        o.shipping_city,
        o.shipping_province,
        o.shipping_country,
        u.id AS user_id,
        u.username,
        COALESCE(u.segment, 'Aficionat') AS user_segment,
        p.id AS product_id,
        p.name AS product_name,
        p.price AS unit_price,
        c.name AS category_name,
        COALESCE(s.name, 'Sense subcategoria') AS subcategory_name,
        oi.quantity,
        (p.price * oi.quantity) AS line_total
    FROM OrderItem oi
    JOIN "Order" o ON oi.order_id = o.id
    JOIN UserAccount u ON o.user_id = u.id
    JOIN Product p ON oi.product_id = p.id
    JOIN Category c ON p.category_id = c.id
    LEFT JOIN Subcategory s ON p.subcategory_id = s.id
    ORDER BY o.created_at, o.id, oi.id
    """

    try:
        cur.execute(sql)
    except sqlite3.OperationalError as e:
        if "Subcategory" in str(e) or "shipping_city" in str(e) or "segment" in str(e):
            print("Executa abans: python3 migrate_tableau_dataset.py")
        else:
            print("Error:", e)
        conn.close()
        return

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No hi ha comandes.")
        return

    fieldnames = [
        "order_id", "order_date", "order_total",
        "shipping_city", "shipping_province", "shipping_country",
        "user_id", "username", "user_segment",
        "product_id", "product_name", "category_name", "subcategory_name",
        "quantity", "unit_price", "line_total",
    ]

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in fieldnames})

    with open(OUT_TSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in fieldnames})

    print(f"Exportades {len(rows)} línies a {OUT_CSV.name} i {OUT_TSV.name}")
    print("A Tableau: connecta techshop_vendes_para_tableau.tsv i tria delimitador Tab.")

if __name__ == "__main__":
    main()
