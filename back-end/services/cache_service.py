"""Servei de caché simple per a productes i dades freqüents.

Aquest mòdul proporciona un sistema de caché en memòria simple
per millorar el rendiment de consultes freqüents.
"""
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from threading import Lock
import time


class CacheEntry:
    """Entrada de caché amb informació de caducitat."""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        """Inicialitza una entrada de caché.
        
        Args:
            value: valor a emmagatzemar
            ttl_seconds: temps de vida en segons (per defecte 5 minuts)
        """
        self.value = value
        self.created_at = datetime.now()
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Comprova si l'entrada ha caducat."""
        return datetime.now() - self.created_at > self.ttl


class SimpleCache:
    """Caché en memòria thread-safe amb TTL."""
    
    def __init__(self):
        """Inicialitza el caché."""
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Obté un valor del caché.
        
        Args:
            key: clau del valor
            
        Returns:
            Valor emmagatzemat o None si no existeix o ha caducat
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Emmagatzema un valor al caché.
        
        Args:
            key: clau del valor
            value: valor a emmagatzemar
            ttl_seconds: temps de vida en segons
        """
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str) -> None:
        """Elimina una entrada del caché.
        
        Args:
            key: clau a eliminar
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Elimina totes les entrades del caché."""
        with self._lock:
            self._cache.clear()
    
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalida entrades que comencen amb un patró.
        
        Útil per invalidar tots els productes quan es modifica un.
        
        Args:
            pattern: patró de prefix per invalidar
        """
        with self._lock:
            keys_to_delete = [key for key in self._cache.keys() if key.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl_seconds: int = 300) -> Any:
        """Obté un valor del caché o el crea si no existeix.
        
        Args:
            key: clau del valor
            factory: funció que crea el valor si no existeix
            ttl_seconds: temps de vida en segons
            
        Returns:
            Valor del caché o creat per la factory
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl_seconds)
        return value
    
    def size(self) -> int:
        """Retorna el nombre d'entrades al caché."""
        with self._lock:
            # Netejar entrades caducades abans de comptar
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(self._cache)


# Instància global del caché
_cache_instance: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """Obté la instància global del caché (singleton).
    
    Returns:
        Instància del caché
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache()
    return _cache_instance


# Exemple d'ús amb decorador
def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """Decorador per cachejar resultats de funcions.
    
    Args:
        ttl_seconds: temps de vida del caché en segons
        key_prefix: prefix per a les claus del caché
        
    Example:
        @cached(ttl_seconds=600, key_prefix="products")
        def get_all_products():
            return ProductRepository(DB_PATH).get_all()
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache = get_cache()
            # Crear clau única basada en arguments
            key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Intentar obtenir del caché
            result = cache.get(key)
            if result is not None:
                return result
            
            # Executar funció i cachejar resultat
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator

