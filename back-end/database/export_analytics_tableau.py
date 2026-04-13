#!/usr/bin/env python3
"""Exporta totes les dades TechShop per Tableau — versió Analytics completa.

Afegeix columnes extra: coordenades geogràfiques, benefici, descompte, estació,
trimestre, dies d'enviament i segment de valor de client.

Una fila = una línia de comanda.
Fitxer: techshop_vendes_analytics.csv / .tsv

Ús: cd back-end/database && python3 export_analytics_tableau.py
"""
import csv
import re
import sqlite3
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"
OUT_CSV = HERE / "techshop_vendes_analytics.csv"
OUT_TSV = HERE / "techshop_vendes_analytics.tsv"

COUNTRY_TO_GEO = {"Espanya": "Spain"}

# Coordenades de totes les ciutats possibles
CITY_COORDS = {
    "Barcelona":        (41.3851,  2.1734),
    "L'Hospitalet":     (41.3599,  2.0997),
    "Badalona":         (41.4505,  2.2474),
    "Girona":           (41.9794,  2.8214),
    "Figueres":         (42.2669,  2.9616),
    "Lleida":           (41.6148,  0.6267),
    "Tarragona":        (41.1189,  1.2445),
    "Reus":             (41.1559,  1.1065),
    "Madrid":           (40.4168, -3.7038),
    "València":         (39.4699, -0.3763),
    "Sevilla":          (37.3886, -5.9823),
    "Bilbao":           (43.2630, -2.9350),
    "Zaragoza":         (41.6488, -0.8891),
    "Sabadell":         (41.5432,  2.1093),
    "Terrassa":         (41.5632,  2.0096),
    "Manresa":          (41.7286,  1.8194),
    "Mataró":           (41.5392,  2.4447),
    "Santa Coloma":     (41.4518,  2.2085),
    "Cornellà":         (41.3556,  2.0721),
    "El Prat":          (41.3257,  2.0946),
    "Vic":              (41.9305,  2.2546),
    "Vilanova":         (41.2244,  1.7259),
    "Tortosa":          (40.8125,  0.5212),
    "Granollers":       (41.6074,  2.2873),
    "Castelldefels":    (41.2796,  1.9773),
}

# Marge de benefici estimat per categoria (%)
CATEGORY_MARGIN = {
    "Plaques":                  0.28,
    "Sensors":                  0.35,
    "LED i llum":               0.42,
    "Components electrònics":   0.38,
    "Displays":                 0.32,
    "Mòduls i shields":         0.30,
    "Motors i Servos":          0.25,
    "Monitores":                0.20,
}
DEFAULT_MARGIN = 0.30

# Cost d'enviament per trams de total de comanda
def _shipping_cost(order_total):
    t = float(order_total or 0)
    if t >= 100:
        return 0.00
    if t >= 60:
        return 2.99
    if t >= 30:
        return 4.99
    return 5.99

# Descompte determinista basat en order_id % 6
DISCOUNT_MAP = {0: 0.0, 1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.05}

def _discount_pct(order_id):
    return DISCOUNT_MAP.get(int(order_id or 0) % 6, 0.0)

# Estació de l'any
def _season(month):
    m = int(month or 1)
    if m in (12, 1, 2):
        return "Hivern"
    if m in (3, 4, 5):
        return "Primavera"
    if m in (6, 7, 8):
        return "Estiu"
    return "Tardor"

# Trimestre
def _quarter(month):
    m = int(month or 1)
    return f"Q{((m - 1) // 3) + 1}"

# Dies d'enviament simulats (deterministes per order_id)
def _days_to_ship(order_id):
    return (int(order_id or 1) % 5) + 1

# Segment de valor de client (Customer Lifetime Value tier)
def _clv_tier(total_spent):
    t = float(total_spent or 0)
    if t >= 800:
        return "Alt"
    if t >= 400:
        return "Mitjà"
    return "Baix"

# Nom del dia de la setmana
WEEKDAY_NAMES = {0: "Diumenge", 1: "Dilluns", 2: "Dimarts", 3: "Dimecres",
                 4: "Dijous", 5: "Divendres", 6: "Dissabte"}

# Rang d'edat per user_id (simulat, realista per perfil)
USER_AGE_RANGE = {
    1: "25-34",   # alumn01 — Professional jove
    2: "18-24",   # maria_tech — Aficionada estudiant
    3: "35-44",   # joan_dev — Desenvolupador sènior
    4: "25-34",   # anna_iot — Professional IoT
    5: "45-54",   # carlos_arduino — Aficionat experimentat
    6: "18-24",   # laura_rasp — Estudiant universitària
}

def _age_range(user_id):
    return USER_AGE_RANGE.get(int(user_id or 0), "35-44")

FIELDNAMES = [
    # Comanda
    "order_id", "order_date", "order_total", "order_year", "order_month",
    "order_quarter", "order_weekday", "order_weekday_name", "order_day_of_month",
    "is_weekend",
    "num_lines_in_order", "total_quantity_in_order", "order_avg_line_total",
    "shipping_cost", "order_total_with_shipping",
    # Ubicació
    "shipping_city", "shipping_province", "shipping_country", "shipping_country_geo",
    "latitude", "longitude",
    "location_num_orders", "location_total_quantity", "location_total_revenue", "location_avg_order_value",
    # Usuari
    "user_id", "username", "user_segment",
    "user_num_orders", "user_total_spent", "user_avg_order_value",
    "clv_tier",
    # Producte
    "product_id", "product_name", "unit_price", "product_stock", "price_tier",
    "product_total_quantity_sold", "product_total_revenue", "product_num_orders",
    "product_rank_in_category_by_revenue",
    # Subcategoria
    "subcategory_id", "subcategory_name",
    "subcategory_num_products", "subcategory_total_stock",
    "subcategory_total_quantity_sold", "subcategory_total_revenue",
    # Categoria
    "category_id", "category_name",
    "category_num_products", "category_total_stock",
    "category_total_quantity_sold", "category_total_revenue",
    # Línia de comanda
    "quantity", "line_total", "line_share_of_order_total",
    "discount_pct", "line_total_after_discount",
    "profit_margin_pct", "profit",
    "days_to_ship",
    "season",
]


def _format_date(value):
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    s_clean = s.split(".")[0].strip()
    try:
        if len(s_clean) >= 19:
            datetime.strptime(s_clean[:19], "%Y-%m-%d %H:%M:%S")
            return s_clean[:10]
        if len(s_clean) >= 10:
            datetime.strptime(s_clean[:10], "%Y-%m-%d")
            return s_clean[:10]
    except ValueError:
        pass
    return s_clean[:10] if len(s_clean) >= 10 else (s_clean or "")


def _fmt_int(v):
    try:
        return int(float(v)) if v is not None and str(v).strip() != "" else 0
    except (TypeError, ValueError):
        return 0


def _fmt_f2(v):
    # Coma com a separador decimal perquè Tableau en locale espanyol ho llegeixi com a número
    try:
        result = float(v) if v is not None and str(v).strip() != "" else 0.0
        return ("%.2f" % result).replace(".", ",")
    except (TypeError, ValueError):
        return "0,00"


INT_COLS = {
    "order_id", "order_year", "order_month", "order_weekday", "order_day_of_month",
    "num_lines_in_order", "total_quantity_in_order", "is_weekend",
    "location_num_orders", "location_total_quantity",
    "user_id", "user_num_orders",
    "product_id", "product_stock", "product_total_quantity_sold",
    "product_num_orders", "product_rank_in_category_by_revenue",
    "subcategory_id", "subcategory_num_products", "subcategory_total_stock", "subcategory_total_quantity_sold",
    "category_id", "category_num_products", "category_total_stock", "category_total_quantity_sold",
    "quantity", "days_to_ship",
}
FLOAT_COLS = {
    "order_total", "order_avg_line_total", "shipping_cost", "order_total_with_shipping",
    "latitude", "longitude",
    "location_total_revenue", "location_avg_order_value",
    "user_total_spent", "user_avg_order_value",
    "unit_price", "product_total_revenue",
    "subcategory_total_revenue", "category_total_revenue",
    "line_total", "line_share_of_order_total",
    "discount_pct", "line_total_after_discount",
    "profit_margin_pct", "profit",
}
DATE_COLS = {"order_date"}


def _enrich_row(row: dict) -> dict:
    out = {}

    # ---- Camps base ----
    for k in (
        "order_id", "order_date", "order_total", "order_year", "order_month",
        "order_weekday", "order_day_of_month", "num_lines_in_order", "total_quantity_in_order",
        "order_avg_line_total", "shipping_city", "shipping_province", "shipping_country",
        "location_num_orders", "location_total_quantity", "location_total_revenue", "location_avg_order_value",
        "user_id", "username", "user_segment", "user_num_orders", "user_total_spent", "user_avg_order_value",
        "product_id", "product_name", "unit_price", "product_stock",
        "product_total_quantity_sold", "product_total_revenue", "product_num_orders",
        "product_rank_in_category_by_revenue",
        "subcategory_id", "subcategory_name", "subcategory_num_products", "subcategory_total_stock",
        "subcategory_total_quantity_sold", "subcategory_total_revenue",
        "category_id", "category_name", "category_num_products", "category_total_stock",
        "category_total_quantity_sold", "category_total_revenue",
        "quantity", "line_total", "line_share_of_order_total",
    ):
        v = row.get(k)
        if k in INT_COLS:
            out[k] = _fmt_int(v)
        elif k in FLOAT_COLS:
            out[k] = _fmt_f2(v)
        elif k in DATE_COLS:
            out[k] = _format_date(v)
        else:
            out[k] = "" if v is None else str(v).strip()

    # ---- Valors derivats: comanda ----
    month = _fmt_int(row.get("order_month"))
    weekday = _fmt_int(row.get("order_weekday"))
    order_id = _fmt_int(row.get("order_id"))
    order_total = float(row.get("order_total") or 0)
    line_total = float(row.get("line_total") or 0)
    category_name = str(row.get("category_name") or "")

    out["order_quarter"] = _quarter(month)
    out["order_weekday_name"] = WEEKDAY_NAMES.get(weekday, "")
    out["is_weekend"] = 1 if weekday in (0, 6) else 0
    out["season"] = _season(month)

    ship_cost = _shipping_cost(order_total)
    out["shipping_cost"] = _fmt_f2(ship_cost)
    out["order_total_with_shipping"] = _fmt_f2(order_total + ship_cost)

    # ---- Ubicació: coordenades ----
    city = str(row.get("shipping_city") or "")
    lat, lon = CITY_COORDS.get(city, (None, None))
    out["latitude"] = _fmt_f2(lat) if lat is not None else ""
    out["longitude"] = _fmt_f2(lon) if lon is not None else ""
    out["shipping_country_geo"] = COUNTRY_TO_GEO.get(
        str(row.get("shipping_country") or ""), str(row.get("shipping_country") or "")
    )

    # ---- Usuari: CLV tier ----
    out["clv_tier"] = _clv_tier(row.get("user_total_spent"))

    # ---- Producte: price tier ----
    try:
        price = float(row.get("unit_price") or 0)
        if price < 20:
            out["price_tier"] = "Low"
        elif price <= 50:
            out["price_tier"] = "Medium"
        else:
            out["price_tier"] = "High"
    except (TypeError, ValueError):
        out["price_tier"] = "Medium"

    # ---- Línia: descompte i benefici ----
    disc = _discount_pct(order_id)
    out["discount_pct"] = _fmt_f2(disc)
    line_after_disc = line_total * (1 - disc)
    out["line_total_after_discount"] = _fmt_f2(line_after_disc)

    margin = CATEGORY_MARGIN.get(category_name, DEFAULT_MARGIN)
    out["profit_margin_pct"] = _fmt_f2(margin)
    out["profit"] = _fmt_f2(line_after_disc * margin)

    # ---- Dies d'enviament ----
    out["days_to_ship"] = _days_to_ship(order_id)

    return out


def main():
    if not DB_PATH.exists():
        print(f"No s'ha trobat {DB_PATH}. Executa init_db.py i migrate_tableau_dataset.py.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    WITH
    order_agg AS (
        SELECT order_id, COUNT(*) AS num_lines, SUM(quantity) AS total_qty
        FROM OrderItem GROUP BY order_id
    ),
    loc_agg AS (
        SELECT o.shipping_city, o.shipping_province, o.shipping_country,
               COUNT(DISTINCT o.id) AS num_orders,
               SUM(oi.quantity) AS total_quantity,
               SUM(p.price * oi.quantity) AS total_revenue
        FROM "Order" o
        LEFT JOIN OrderItem oi ON oi.order_id = o.id
        LEFT JOIN Product p ON oi.product_id = p.id
        WHERE o.shipping_country IS NOT NULL AND o.shipping_country != ''
        GROUP BY o.shipping_city, o.shipping_province, o.shipping_country
    ),
    user_agg AS (
        SELECT u.id AS user_id, COUNT(DISTINCT o.id) AS num_orders,
               COALESCE(SUM(o.total), 0) AS total_spent
        FROM UserAccount u LEFT JOIN "Order" o ON o.user_id = u.id
        GROUP BY u.id
    ),
    prod_agg AS (
        SELECT p.id AS product_id,
               COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
               COALESCE(SUM(p.price * oi.quantity), 0) AS total_revenue,
               COUNT(DISTINCT oi.order_id) AS num_orders
        FROM Product p LEFT JOIN OrderItem oi ON oi.product_id = p.id
        GROUP BY p.id
    ),
    cat_agg AS (
        SELECT c.id AS category_id,
               COUNT(DISTINCT p.id) AS num_products,
               COALESCE(SUM(p.stock), 0) AS total_stock,
               COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
               COALESCE(SUM(p.price * oi.quantity), 0) AS total_revenue
        FROM Category c
        LEFT JOIN Product p ON p.category_id = c.id
        LEFT JOIN OrderItem oi ON oi.product_id = p.id
        GROUP BY c.id
    ),
    subcat_agg AS (
        SELECT s.id AS subcategory_id,
               COUNT(DISTINCT p.id) AS num_products,
               COALESCE(SUM(p.stock), 0) AS total_stock,
               COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
               COALESCE(SUM(p.price * oi.quantity), 0) AS total_revenue
        FROM Subcategory s
        LEFT JOIN Product p ON p.subcategory_id = s.id
        LEFT JOIN OrderItem oi ON oi.product_id = p.id
        GROUP BY s.id
    ),
    product_rank_in_cat AS (
        SELECT p.id AS product_id, p.category_id,
               RANK() OVER (PARTITION BY p.category_id ORDER BY COALESCE(SUM(p.price * oi.quantity), 0) DESC) AS rk
        FROM Product p
        LEFT JOIN OrderItem oi ON oi.product_id = p.id
        GROUP BY p.id, p.category_id
    )
    SELECT
        o.id AS order_id,
        o.created_at AS order_date,
        o.total AS order_total,
        CAST(strftime('%Y', o.created_at) AS INTEGER) AS order_year,
        CAST(strftime('%m', o.created_at) AS INTEGER) AS order_month,
        CAST(strftime('%w', o.created_at) AS INTEGER) AS order_weekday,
        CAST(strftime('%d', o.created_at) AS INTEGER) AS order_day_of_month,
        oa.num_lines AS num_lines_in_order,
        oa.total_qty AS total_quantity_in_order,
        (o.total * 1.0 / NULLIF(oa.num_lines, 0)) AS order_avg_line_total,
        o.shipping_city, o.shipping_province, o.shipping_country,
        la.num_orders AS location_num_orders,
        la.total_quantity AS location_total_quantity,
        la.total_revenue AS location_total_revenue,
        (la.total_revenue * 1.0 / NULLIF(la.num_orders, 0)) AS location_avg_order_value,
        u.id AS user_id,
        u.username,
        COALESCE(u.segment, 'Aficionat') AS user_segment,
        ua.num_orders AS user_num_orders,
        ua.total_spent AS user_total_spent,
        (ua.total_spent * 1.0 / NULLIF(ua.num_orders, 0)) AS user_avg_order_value,
        p.id AS product_id,
        p.name AS product_name,
        p.price AS unit_price,
        p.stock AS product_stock,
        pa.total_quantity_sold AS product_total_quantity_sold,
        pa.total_revenue AS product_total_revenue,
        pa.num_orders AS product_num_orders,
        pr.rk AS product_rank_in_category_by_revenue,
        s.id AS subcategory_id,
        COALESCE(s.name, 'Sense subcategoria') AS subcategory_name,
        COALESCE(sa.num_products, 0) AS subcategory_num_products,
        COALESCE(sa.total_stock, 0) AS subcategory_total_stock,
        COALESCE(sa.total_quantity_sold, 0) AS subcategory_total_quantity_sold,
        COALESCE(sa.total_revenue, 0) AS subcategory_total_revenue,
        c.id AS category_id,
        c.name AS category_name,
        ca.num_products AS category_num_products,
        ca.total_stock AS category_total_stock,
        ca.total_quantity_sold AS category_total_quantity_sold,
        ca.total_revenue AS category_total_revenue,
        oi.quantity,
        (p.price * oi.quantity) AS line_total,
        ((p.price * oi.quantity) * 1.0 / NULLIF(o.total, 0)) AS line_share_of_order_total
    FROM OrderItem oi
    JOIN "Order" o ON oi.order_id = o.id
    JOIN UserAccount u ON o.user_id = u.id
    JOIN Product p ON oi.product_id = p.id
    JOIN Category c ON p.category_id = c.id
    LEFT JOIN Subcategory s ON p.subcategory_id = s.id
    LEFT JOIN order_agg oa ON oa.order_id = o.id
    LEFT JOIN loc_agg la ON la.shipping_city = o.shipping_city
                         AND la.shipping_province = o.shipping_province
                         AND la.shipping_country = o.shipping_country
    LEFT JOIN user_agg ua ON ua.user_id = u.id
    LEFT JOIN prod_agg pa ON pa.product_id = p.id
    LEFT JOIN product_rank_in_cat pr ON pr.product_id = p.id AND pr.category_id = c.id
    LEFT JOIN subcat_agg sa ON sa.subcategory_id = s.id
    LEFT JOIN cat_agg ca ON ca.category_id = c.id
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
        print("No hi ha comandes a la base de dades.")
        return

    for path, delim in [(OUT_CSV, ";"), (OUT_TSV, "\t")]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter=delim)
            w.writeheader()
            for row in rows:
                w.writerow(_enrich_row(dict(row)))

    print(f"Export completat: {len(rows)} files, {len(FIELDNAMES)} columnes")
    print(f"  → {OUT_CSV.name}  (delimitador ;)")
    print(f"  → {OUT_TSV.name}  (delimitador Tab, recomanat per Tableau)")
    print()
    print("Columnes noves respecte a la versió anterior:")
    new_cols = [
        "order_quarter", "order_weekday_name", "is_weekend",
        "shipping_cost", "order_total_with_shipping",
        "latitude", "longitude",
        "clv_tier",
        "discount_pct", "line_total_after_discount",
        "profit_margin_pct", "profit",
        "days_to_ship", "season",
    ]
    for c in new_cols:
        print(f"    + {c}")


if __name__ == "__main__":
    main()
