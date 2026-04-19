"""Servei de sincronització amb Google Sheets.

Sincronitza els productes recomanats i el seu stock amb un full de Google Sheets
per poder consultar-los des de Google Sheets o via MCP.
Si no hi ha TECHSHOP_SPREADSHEET_ID, es pot crear un document nou.
"""
import os
from typing import List, Optional, Tuple
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parent  # .../back-end/services
_BACKEND_ROOT = _SERVICE_ROOT.parent           # .../back-end
_PROJECT_ROOT = _BACKEND_ROOT.parent          # .../5073-tech

# Tipus: llista de productes (id, name, price, stock)
ProductRow = Tuple[int, str, float, int]

# Resultat: (èxit, missatge, url_opcional)
SyncResult = Tuple[bool, str, Optional[str]]


def _get_credentials_path() -> Optional[str]:
    """Ruta al fitxer JSON de credencials del Service Account."""
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


def _resolve_credentials_file(raw: str) -> Optional[Path]:
    """Resol rutes relatives de forma robusta (cwd, arrel del repo i carpeta back-end)."""
    p = Path(raw.strip())
    if p.is_file():
        return p.resolve()

    candidates: List[Path] = []
    if not p.is_absolute():
        candidates.extend(
            [
                (Path.cwd() / p).resolve(),
                (_PROJECT_ROOT / p).resolve(),
                (_BACKEND_ROOT / p).resolve(),
            ]
        )
        # Si el .env apunta a "back-end/..." però Flask s'executa des de back-end/, evita duplicar el prefix
        parts = p.as_posix().lstrip("./").split("/", 1)
        if len(parts) == 2 and parts[0] == "back-end":
            inner = Path(parts[1])
            candidates.extend(
                [
                    (_PROJECT_ROOT / p).resolve(),  # ja inclòs, però explícit
                    (_BACKEND_ROOT / inner).resolve(),
                    (Path.cwd() / inner).resolve(),
                ]
            )

    for c in candidates:
        if c.is_file():
            return c
    return None


def _get_spreadsheet_id() -> Optional[str]:
    """ID del full de Google Sheets (de la URL)."""
    return os.environ.get("TECHSHOP_SPREADSHEET_ID")

def _get_sheet_name() -> str:
    """Nom de la pestanya/fulle del document."""
    return os.environ.get("TECHSHOP_SHEET_NAME", "Recomanats i Stock")


def is_sheets_configured() -> bool:
    """Comprova si Google Sheets està configurat (només calen credencials)."""
    raw = _get_credentials_path()
    if not raw:
        return False
    return _resolve_credentials_file(raw) is not None


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

    resolved = _resolve_credentials_file(creds_path)
    if not resolved:
        return False, f"Fitxer de credencials no trobat: {creds_path}", None
    creds_path = str(resolved)

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


def _get_order_sheet_name() -> str:
    """Nom del full on s'appendeixen les compres (no es sobreescriu el full de recomanacions)."""
    return os.environ.get("TECHSHOP_ORDER_SHEET_NAME", "Comandes")


def sync_order_invoice_to_sheets(invoice_data: dict, create_if_missing: bool = True) -> SyncResult:
    """
    Afegeix (append) una compra al Google Sheet, sense esborrar el full de recomanacions.

    Args:
        invoice_data: diccionari retornat per invoice_controller.get_invoice_data(...)
        create_if_missing: si True i no hi ha TECHSHOP_SPREADSHEET_ID, crea un document nou

    Returns:
        (èxit, missatge, url_del_sheet o None)
    """
    creds_path = _get_credentials_path()
    spreadsheet_id = _get_spreadsheet_id()

    if not creds_path:
        return False, "Defineix GOOGLE_APPLICATION_CREDENTIALS (ruta al JSON del Service Account).", None

    resolved = _resolve_credentials_file(creds_path)
    if not resolved:
        return False, f"Fitxer de credencials no trobat: {creds_path}", None
    creds_path = str(resolved)

    if not spreadsheet_id and not create_if_missing:
        return False, "Defineix TECHSHOP_SPREADSHEET_ID o deixa que es creï un document nou.", None

    order = invoice_data.get("order")
    user = invoice_data.get("user")
    items = invoice_data.get("invoice_items") or []
    order_id = invoice_data.get("order_id")

    if order is None or order_id is None:
        return False, "Dades de factura incompletes (falta comanda).", None

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
        else:
            spreadsheet = gc.create("TechShop - Recomanats i Stock")
            spreadsheet_id = spreadsheet.id

        sheet_title = _get_order_sheet_name()
        try:
            worksheet = spreadsheet.worksheet(sheet_title)
        except Exception:
            worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=2000, cols=20)

        # Capçaleres (només si el full està buit)
        existing = worksheet.row_values(1)
        if not existing:
            headers = [
                "Order ID",
                "Data",
                "Usuari",
                "Email",
                "Ciutat",
                "Província",
                "País",
                "Total comanda (€)",
                "Product ID",
                "Producte",
                "Quantitat",
                "Preu unitari (€)",
                "Subtotal (€)",
            ]
            worksheet.append_row(headers, value_input_option="USER_ENTERED")

        created_at = str(getattr(order, "created_at", "") or "")
        date_only = created_at[:10] if len(created_at) >= 10 else created_at
        username = getattr(user, "username", "") if user else ""
        email = getattr(user, "email", "") if user else ""

        city = getattr(order, "shipping_city", None) or ""
        province = getattr(order, "shipping_province", None) or ""
        country = getattr(order, "shipping_country", None) or ""
        total = float(getattr(order, "total", 0.0) or 0.0)

        rows_to_append = []
        for it in items:
            product = it.get("product")
            qty = int(it.get("quantity") or 0)
            unit = float(it.get("unit_price") or 0.0)
            subtotal = float(it.get("subtotal") or 0.0)
            pid = int(getattr(product, "id", 0) or 0) if product else 0
            pname = str(getattr(product, "name", "") or "") if product else ""

            rows_to_append.append(
                [
                    int(order_id),
                    date_only,
                    username,
                    email,
                    city,
                    province,
                    country,
                    round(total, 2),
                    pid,
                    pname,
                    qty,
                    round(unit, 2),
                    round(subtotal, 2),
                ]
            )

        if rows_to_append:
            worksheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")

        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit#gid={worksheet.id}"
        return True, f"Comanda #{order_id} afegida al full '{sheet_title}' de Google Sheets.", url
    except Exception as e:
        msg = str(e).strip() or repr(e)
        if hasattr(e, "response") and getattr(e.response, "text", None):
            msg = f"{msg} | {e.response.text[:200]}"
        return False, f"Error en exportar la comanda a Google Sheets: {type(e).__name__}: {msg}", None
