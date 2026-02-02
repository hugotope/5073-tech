"""Servei de sincronització amb Google Sheets.

Sincronitza els productes recomanats i el seu stock amb un full de Google Sheets
per poder consultar-los des de Google Sheets o via MCP.
Si no hi ha TECHSHOP_SPREADSHEET_ID, es pot crear un document nou.
"""
import os
from typing import List, Optional, Tuple
from pathlib import Path

# Tipus: llista de productes (id, name, price, stock)
ProductRow = Tuple[int, str, float, int]

# Resultat: (èxit, missatge, url_opcional)
SyncResult = Tuple[bool, str, Optional[str]]


def _get_credentials_path() -> Optional[str]:
    """Ruta al fitxer JSON de credencials del Service Account."""
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


def _get_spreadsheet_id() -> Optional[str]:
    """ID del full de Google Sheets (de la URL)."""
    return os.environ.get("TECHSHOP_SPREADSHEET_ID")

def _get_sheet_name() -> str:
    """Nom de la pestanya/fulle del document."""
    return os.environ.get("TECHSHOP_SHEET_NAME", "Recomanats i Stock")


def is_sheets_configured() -> bool:
    """Comprova si Google Sheets està configurat (només calen credencials)."""
    return bool(_get_credentials_path())


def sync_recommended_products_to_sheets(
    products: List[ProductRow],
    db_path: Optional[Path] = None,
    create_if_missing: bool = True,
) -> SyncResult:
    """
    Escriu la llista de productes recomanats i stock al Google Sheet.
    Si TECHSHOP_SPREADSHEET_ID no està definit i create_if_missing és True,
    crea un document nou i retorna la URL.

    Args:
        products: Llista de tuples (id, name, price, stock).
        db_path: No s'utilitza; es manté per compatibilitat.
        create_if_missing: Si True i no hi ha ID, crea un nou Google Sheet.

    Returns:
        (èxit, missatge, url_del_sheet o None)
    """
    creds_path = _get_credentials_path()
    spreadsheet_id = _get_spreadsheet_id()

    if not creds_path:
        return False, "Defineix GOOGLE_APPLICATION_CREDENTIALS (ruta al JSON del Service Account).", None

    # Resoldre a ruta absoluta per evitar PermissionError amb rutes relatives
    creds_path = str(Path(creds_path).resolve())
    if not os.path.isfile(creds_path):
        return False, f"Fitxer de credencials no trobat: {creds_path}", None

    if not spreadsheet_id and not create_if_missing:
        return False, "Defineix TECHSHOP_SPREADSHEET_ID o deixa que es creï un document nou.", None

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(credentials)

        if spreadsheet_id:
            spreadsheet = gc.open_by_key(spreadsheet_id)
            # Utilitzar la primera fulla del document (evita problemes de nom o permisos)
            worksheet = spreadsheet.sheet1
        else:
            spreadsheet = gc.create("TechShop - Recomanats i Stock")
            spreadsheet_id = spreadsheet.id
            worksheet = spreadsheet.sheet1

        headers = ["ID", "Producte", "Preu (€)", "Stock", "Observacions"]
        rows = [headers]
        for product_id, name, price, stock in products:
            obs = "Sense stock" if stock <= 0 else ""
            rows.append([product_id, name, round(price, 2), stock, obs])

        if rows:
            worksheet.clear()
            worksheet.update("A1", rows, value_input_option="USER_ENTERED")

        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit"
        return True, f"S'han sincronitzat {len(products)} productes a Google Sheets.", url
    except PermissionError:
        raise  # deixar propagar per veure el traceback al script
    except Exception as e:
        msg = str(e).strip() or repr(e)
        if hasattr(e, "response") and getattr(e.response, "text", None):
            msg = f"{msg} | {e.response.text[:200]}"
        return False, f"Error en sincronitzar amb Google Sheets: {type(e).__name__}: {msg}", None
