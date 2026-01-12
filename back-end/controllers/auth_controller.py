"""Controlador per a l'autenticació d'usuaris.

Aquest mòdul conté la lògica de negoci relacionada amb l'autenticació,
incloent les funcions de registre i login d'usuaris.

Regles de negoci implementades:
- Validació de nom d'usuari (4-20 caràcters)
- Validació de contrasenya (mínim 8 caràcters)
- Validació d'email
- Verificació d'usuaris i emails únics
"""
import hashlib
import sqlite3
from typing import Tuple, Optional
from pathlib import Path
from models import UserAccount


def register_user(username: str, password: str, email: str, db_path: Path) -> Tuple[bool, str]:
    """Registra un nou usuari al sistema.
    
    Args:
        username: nom d'usuari (4-20 caràcters)
        password: contrasenya (mínim 8 caràcters)
        email: correu electrònic vàlid
        db_path: ruta a la base de dades
        
    Returns:
        Tupla (èxit, missatge)
    """
    # Validacions
    if len(username) < 4 or len(username) > 20:
        return False, "El nom d'usuari ha de tenir entre 4 i 20 caràcters"
    
    if len(password) < 8:
        return False, "La contrasenya ha de tenir com a mínim 8 caràcters"
    
    if not email or '@' not in email:
        return False, "Correu electrònic no vàlid"
    
    # Comprovar si l'usuari ja existeix
    existing_user = UserAccount.get_by_username(username, db_path)
    if existing_user:
        return False, "Aquest nom d'usuari ja està en ús"
    
    # Comprovar si l'email ja existeix
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM UserAccount WHERE email = ?", (email,))
            if cur.fetchone():
                return False, "Aquest correu electrònic ja està registrat"
    except sqlite3.Error:
        return False, "Error al comprovar el correu electrònic"
    
    # Generar hash de la contrasenya
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Crear l'usuari
    try:
        user_id = UserAccount.create(username, password_hash, email, db_path)
        return True, f"Usuari registrat amb èxit! Benvingut, {username}"
    except sqlite3.IntegrityError:
        return False, "Error al registrar l'usuari. Potser el nom d'usuari o email ja existeixen"
    except Exception as e:
        return False, f"Error inesperat al registrar: {str(e)}"


def login_user(username: str, password: str, db_path: Path) -> Tuple[bool, str, Optional[UserAccount]]:
    """Autentica un usuari amb nom d'usuari i contrasenya.
    
    Args:
        username: nom d'usuari
        password: contrasenya
        db_path: ruta a la base de dades
        
    Returns:
        Tupla (èxit, missatge, usuari o None)
    """
    if not username or not password:
        return False, "Has d'introduir nom d'usuari i contrasenya", None
    
    # Autenticar l'usuari
    user = UserAccount.authenticate(username, password, db_path)
    
    if user is None:
        return False, "Nom d'usuari o contrasenya incorrectes", None
    
    return True, f"Benvingut de nou, {username}!", user

