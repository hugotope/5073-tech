"""
Utilitats de seguretat per a l'aplicació TechShop.

Aquest mòdul centralitza funcionalitats com la generació i validació
de tokens CSRF i permet, si es vol, estendre fàcilment amb altres
mesures de *hardening* (per exemple, generació de claus, helpers JWT, etc.).
"""
import os
import secrets
from flask import session, request, abort


def get_secret_key() -> str:
    """Obté la SECRET_KEY de l'entorn amb un valor per defecte segur en desenvolupament.

    Returns:
        Clau secreta per a Flask.
    """
    return os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")


def generate_csrf_token() -> str:
    """Genera (si cal) i retorna un token CSRF emmagatzemat a la sessió.

    Aquest enfocament lleuger evita afegir dependències externes i
    proporciona una protecció bàsica contra CSRF.
    """
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["_csrf_token"] = token
    return token


def validate_csrf() -> None:
    """Valida el token CSRF per a peticions d'escriptura basades en formulari.

    Per simplicitat, només s'aplica a peticions POST que no siguin de l'API
    (per exemple, rutes que comencen per /api/ poden utilitzar altres mecanismes
    com headers X-CSRF-Token).

    Raises:
        werkzeug.exceptions.HTTPException: Si el token és invàlid o falta (403).
    """
    # Només validar en mètodes que modifiquen estat i que no siguin rutes d'API
    if request.method != "POST":
        return
    if request.path.startswith("/api/"):
        return

    sent_token = request.form.get("csrf_token", "")
    session_token = session.get("_csrf_token", "")
    if not sent_token or not session_token or sent_token != session_token:
        abort(403)


