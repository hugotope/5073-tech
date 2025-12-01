"""Pruebas unitarias para autenticación de usuarios.

Este módulo contiene las pruebas para el método authenticate de UserAccount.
"""
import unittest
import sqlite3
import tempfile
from pathlib import Path
import sys

from werkzeug.security import generate_password_hash

# Agregar el directorio padre al path para importar los modelos
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserAccount


class TestAuthentication(unittest.TestCase):
    """Pruebas unitarias para autenticación de usuarios."""
    
    def setUp(self):
        """Configuración inicial antes de cada prueba.
        
        Crea una base de datos temporal y la inicializa con el esquema
        y datos de prueba necesarios.
        """
        # Crear base de datos temporal
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = Path(self.temp_db.name)
        
        # Inicializar esquema de base de datos
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA foreign_keys = ON;')
            conn.execute("""
                CREATE TABLE IF NOT EXISTS UserAccount (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(20) NOT NULL UNIQUE CHECK(length(username) BETWEEN 4 AND 20),
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(64) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        
        # Crear usuario de prueba 'alice' con password '1234'
        salt = "testsalt_alice"
        password_hash_alice = generate_password_hash(
            f"{salt}1234", method="pbkdf2:sha256", salt_length=16
        )
        UserAccount.create('alice', password_hash_alice, salt, 'alice@example.com', self.db_path)
    
    def tearDown(self):
        """Limpieza después de cada prueba.
        
        Elimina la base de datos temporal.
        """
        # Cerrar cualquier conexión pendiente
        import gc
        gc.collect()
        
        # Intentar eliminar el archivo, con manejo de errores para Windows
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except (PermissionError, OSError):
                # En Windows, a veces el archivo puede estar bloqueado temporalmente
                # Se intentará eliminar en la siguiente ejecución
                pass
    
    def test_tc01_autenticacion_valida(self):
        """TC01: Autenticación válida.
        
        Verifica que un usuario con credenciales correctas pueda autenticarse correctamente.
        Entrada: username='alice', password='1234'
        Resultado Esperado: Se devuelve un objeto UserAccount con los datos del usuario.
        """
        result = UserAccount.authenticate('alice', '1234', self.db_path)
        
        self.assertIsNotNone(result, "Debería devolver un objeto UserAccount")
        self.assertIsInstance(result, UserAccount, "El resultado debe ser una instancia de UserAccount")
        self.assertEqual(result.username, 'alice', "El username debe ser 'alice'")
        self.assertEqual(result.email, 'alice@example.com', "El email debe ser correcto")
    
    def test_tc02_contrasena_incorrecta(self):
        """TC02: Contraseña incorrecta.
        
        Verifica que no se autentique un usuario con contraseña incorrecta.
        Entrada: username='alice', password='incorrecta'
        Resultado Esperado: Se devuelve None.
        """
        result = UserAccount.authenticate('alice', 'incorrecta', self.db_path)
        
        self.assertIsNone(result, "Debería devolver None cuando la contraseña es incorrecta")
    
    def test_tc03_usuario_inexistente(self):
        """TC03: Usuario inexistente.
        
        Verifica que el método maneje un nombre de usuario no existente sin lanzar errores.
        Entrada: username='carol', password='whatever'
        Resultado Esperado: Se devuelve None.
        """
        result = UserAccount.authenticate('carol', 'whatever', self.db_path)
        
        self.assertIsNone(result, "Debería devolver None cuando el usuario no existe")
    
    def test_tc04_creacion_y_autenticacion_nuevo_usuario(self):
        """TC04: Creación y autenticación de nuevo usuario.
        
        Prueba la creación e inicio de sesión de un nuevo usuario en la base de datos.
        Entrada: username='new_user', password='pass123'
        Resultado Esperado: El usuario se autentica correctamente y devuelve un objeto UserAccount.
        """
        # Crear nuevo usuario utilizando el mismo esquema de hash que en producción
        salt = "testsalt_new_user"
        password_hash = generate_password_hash(
            f"{salt}pass123", method="pbkdf2:sha256", salt_length=16
        )
        user_id = UserAccount.create('new_user', password_hash, salt, 'new_user@example.com', self.db_path)
        
        self.assertIsNotNone(user_id, "El usuario debería haberse creado correctamente")
        
        # Intentar autenticar el nuevo usuario
        result = UserAccount.authenticate('new_user', 'pass123', self.db_path)
        
        self.assertIsNotNone(result, "Debería devolver un objeto UserAccount")
        self.assertIsInstance(result, UserAccount, "El resultado debe ser una instancia de UserAccount")
        self.assertEqual(result.username, 'new_user', "El username debe ser 'new_user'")
        self.assertEqual(result.id, user_id, "El ID debe coincidir con el usuario creado")
    
    def test_tc05_conexion_base_datos_test(self):
        """TC05: Conexión a base de datos de test.
        
        Verifica que el modelo use la base de datos temporal configurada para pruebas.
        Entrada: DB_PATH='tests/test_techshop.db'
        Resultado Esperado: La conexión se establece correctamente sin afectar la base de datos principal.
        """
        # Verificar que la base de datos temporal existe
        self.assertTrue(self.db_path.exists(), "La base de datos de prueba debe existir")
        
        # Verificar que podemos conectarnos y consultar
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM UserAccount")
            count = cur.fetchone()[0]
            self.assertGreater(count, 0, "Debe haber al menos un usuario en la base de datos de prueba")
        
        # Verificar que podemos autenticar usando la base de datos de prueba
        result = UserAccount.authenticate('alice', '1234', self.db_path)
        self.assertIsNotNone(result, "Debe poder autenticar usando la base de datos de prueba")


if __name__ == '__main__':
    unittest.main()

