# Tableau Story – TechShop

Passos per preparar les dades i crear la Story a Tableau (tasca individual).

## 1. Requisits del dataset (ja coberts)

- **Mínim 100 productes**: la base de dades en té (categories + subcategories).
- **Categoria i Subcategoria**: taules `Category` i `Subcategory`; cada producte té `category_id` i `subcategory_id`.
- **Ubicacions**: les comandes tenen `shipping_city`, `shipping_province`, `shipping_country` (per mapes).
- **Perfil d'usuari**: `UserAccount.segment` (Professional, Aficionat, Educació).

## 2. Exportar dades per a Tableau

Des de la carpeta `back-end/database`:

```bash
# Si encara no l'has fet: migració que afegeix Subcategoria, segment i ubicacions
python3 migrate_tableau_dataset.py

# Exporta un CSV amb una fila per línia de comanda (vendes)
python3 export_tableau_csv.py
```

Es generen **`techshop_vendes_para_tableau.csv`** i **`techshop_vendes_para_tableau.tsv`** (recomanat per Tableau) a la mateixa carpeta.

## 3. Connexió a Tableau

- Obre **Tableau Desktop** o **Tableau Public**.
- **Connectar** → **Fitxer de text** → tria `techshop_vendes_para_tableau.tsv` i com a delimitador **Tab** (o el CSV amb **Punto y coma**).
- Assegura’t que Tableau reconeix:
  - **order_date** com a data.
  - **shipping_country**, **shipping_province**, **shipping_city** per a mapes (geografia).
  - **category_name**, **subcategory_name**, **product_name** per a la jerarquia de producte.
  - **user_segment** per a l’anàlisi per perfil.

## 4. Què ha d’incloure la Story (mínim)

1. **Vendes per producte i jerarquia**
   - Comparatives Categoria → Subcategoria → Producte.
   - Top productes / categories (barres o taules).

2. **Anàlisi geogràfica (mapa)**
   - Mapa amb vendes/comandes per ubicació (país, província o ciutat).
   - Zoom i agrupació per província / regió / país.

3. **Anàlisi per perfil d’usuari**
   - Quin segment compra més què (user_segment vs categoria/producte).
   - Comparatives i patrons (ex.: categories preferides per segment).

4. **Filtres i interacció**
   - Filtres útils: **order_date**, categoria/subcategoria, zona geogràfica, **user_segment**.

## 5. Entrega

- Publicar el workbook a **Tableau Public**.
- Lliurar l’**enllaç** al pou abans del **23/02/26 a les 14:30**.
- Presentació en directe (~10 min) fent servir només el link del Tableau.

## Connexió directa a la base de dades (alternativa)

En lloc del CSV, pots connectar Tableau directament a la base de dades:

- **Connexió** → **SQLite** → tria `back-end/database/db.sqlite3`.
- Crea una vista (query) o joins que reprodueixin el mateix nivell de detall que el CSV (comandes + productes + categories + subcategories + usuaris + ubicacions).

El CSV exportat ja ofereix aquesta vista denormalitzada per comoditat.
