#!/usr/bin/env python3
"""
Script per crear/sincronitzar el Google Sheet de recomanats i stock des de terminal.

Necessites només GOOGLE_APPLICATION_CREDENTIALS al .env (ruta al JSON del Service Account).
Opcional: TECHSHOP_SPREADSHEET_ID si ja tens un document; si no, se'n crea un de nou.

Com executar (des de la arrel del projecte 5073-tech):

  # Amb entorn virtual activat
  python back-end/scripts/sync_sheets.py

  # O des de back-end
  cd back-end && python scripts/sync_sheets.py
"""
import sys
from pathlib import Path

# Arrel del projecte (5073-tech) i back-end
ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = Path(__file__).resolve().parent.parent

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Carregar variables d'entorn
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
load_dotenv(BACKEND / ".env")

# Ara importem després de tenir el path
from controllers.recommendation_controller import get_recommended_products
from services.sheets_sync_service import sync_recommended_products_to_sheets

DB_PATH = BACKEND / "database" / "db.sqlite3"


def main():
    import os

    # Assegurar que el directori de treball és la arrel del projecte
    os.chdir(ROOT)

    # Ruta absoluta per a les credencials (evita PermissionError amb rutes relatives)
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds and not os.path.isabs(creds):
        abs_creds = (ROOT / creds).resolve()
        if abs_creds.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(abs_creds)

    if not DB_PATH.exists():
        print("Error: No s'ha trobat la base de dades:", DB_PATH)
        print("Executa abans init_db o l'aplicació Flask.")
        sys.exit(1)

    print("Obtenint productes recomanats (més populars)...")
    recommended = get_recommended_products(user_id=None, db_path=DB_PATH, limit=50)
    rows = [(p.id, p.name, p.price, p.stock) for p in recommended]
    print(f"  -> {len(rows)} productes")

    if not rows:
        print("No hi ha productes a enviar. Afegeix productes a la base de dades.")
        sys.exit(0)

    print("Sincronitzant amb Google Sheets (es crea un document nou si cal)...")
    try:
        success, message, url = sync_recommended_products_to_sheets(
            rows, db_path=DB_PATH, create_if_missing=True
        )
    except PermissionError:
        import traceback
        print("PermissionError (traceback per localitzar on falla):")
        traceback.print_exc()
        sys.exit(1)

    if success:
        print("OK:", message)
        if url:
            print()
            print("  Document creat. Obre'l aquí:")
            print("  ", url)
            print()
            print("  Per a la propera vegada, afegeix al .env:")
            print("  TECHSHOP_SPREADSHEET_ID=<ID del document (de la URL)>")
    else:
        print("Error:", message)
        if not message.strip():
            import traceback
            print("Detalls (traceback):")
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
