# Suggeriments d'Optimització per a TechShop

Aquest document conté suggeriments d'optimització per millorar el rendiment, mantenibilitat i escalabilitat del projecte.

## 1. Gestió Eficient del Carretó

### Problemes Actuals
- **N+1 Query Problem**: En la vista del carretó, es carreguen TOTS els productes (`Product.get_all()`) per després buscar els que estan al carretó
- **Múltiples consultes**: Cada producte del carretó requereix una consulta individual
- **Falta de validació en temps real**: El stock no es valida quan es mostra el carretó
- **Càlcul ineficient del total**: Es recalculen tots els preus cada vegada

### Solucions Proposades

#### 1.1. Consulta Optimitzada del Carretó
```python
# En lloc de:
products = Product.get_all(DB_PATH)  # Carrega TOTS els productes
for product_id in cart_items:
    product = next((p for p in products if p.id == int(product_id)), None)

# Millor:
product_ids = [int(pid) for pid in cart_items.keys()]
products = Product.get_by_ids(product_ids, DB_PATH)  # Consulta única amb IN
```

#### 1.2. Caché de Productes en Memòria
- Implementar un sistema de caché simple per productes freqüents
- Invalidar la caché quan es modifica el stock

#### 1.3. Validació de Stock en Temps Real
- Validar el stock quan es mostra el carretó
- Mostrar alertes si un producte ja no està disponible

#### 1.4. Emmagatzematge del Total al Carretó
- Guardar el total calculat a la sessió
- Recalcular només quan es modifica el carretó

## 2. Patró Repositori per Accés a Base de Dades

### Problemes Actuals
- Cada mètode estàtic crea una nova connexió
- Codi duplicat de connexió a la base de dades
- No hi ha gestió centralitzada de transaccions
- Difícil de testar (acoblament amb sqlite3)

### Solució: Implementar Patró Repositori

#### 2.1. Estructura del Repositori
```
repositories/
  ├── __init__.py
  ├── base_repository.py      # Classe base amb gestió de connexió
  ├── product_repository.py   # Repositori de productes
  ├── user_repository.py      # Repositori d'usuaris
  └── order_repository.py     # Repositori de comandes
```

#### 2.2. Beneficis
- **Reutilització de connexió**: Una sola connexió per transacció
- **Testabilitat**: Fàcil de mockejar per a tests
- **Abstracció**: Canviar de SQLite a PostgreSQL sense modificar la lògica de negoci
- **Transaccions**: Gestió explícita de transaccions

## 3. Optimitzacions de Consultes SQL

### 3.1. Consultes Batch
```python
# En lloc de múltiples consultes:
for product_id in product_ids:
    product = Product.get_by_id(product_id, db_path)

# Una sola consulta:
products = Product.get_by_ids(product_ids, db_path)
# SQL: SELECT * FROM Product WHERE id IN (?, ?, ?, ...)
```

### 3.2. Índexs de Base de Dades
- Afegir índexs per consultes freqüents:
  - `idx_product_stock` per filtrar per stock
  - `idx_order_user_created` per consultes de comandes per usuari

### 3.3. Consultes amb JOINs
- En lloc de múltiples consultes, usar JOINs quan sigui possible
- Exemple: Carregar comandes amb els seus items en una sola consulta

## 4. Gestió de Sessió i Carretó

### 4.1. Carretó Persistit (Opcional)
- Guardar el carretó a la base de dades per usuaris autenticats
- Permet recuperar el carretó entre sessions
- Sincronitzar entre dispositius

### 4.2. Serialització Eficient
- El carretó actual és un diccionari simple (bé per a sessions petites)
- Per carretons grans, considerar compressió o emmagatzematge extern

### 4.3. Validació de Sessió
- Validar que la sessió no estigui corrupta
- Netejar carretons antics periòdicament

## 5. Caché i Rendiment

### 5.1. Caché de Productes
- Productes que no canvien sovint (nom, preu) poden ser en caché
- Invalidar quan es modifica stock o preu

### 5.2. Caché de Recomanacions
- Les recomanacions poden ser en caché per un temps determinat
- Recalcular només quan hi ha noves compres

### 5.3. Lazy Loading
- Carregar productes només quan es necessiten
- Paginació per llistes grans

## 6. Gestió d'Errors i Transaccions

### 6.1. Context Manager per Transaccions
```python
with db_transaction(db_path) as conn:
    # Totes les operacions dins d'una transacció
    # Rollback automàtic en cas d'error
```

### 6.2. Retry Logic
- Per operacions crítiques, implementar retry amb backoff exponencial
- Especialment útil per a operacions de stock

### 6.3. Locking Optimista
- Per evitar condicions de carrera en actualitzacions de stock
- Usar versioning o timestamps

## 7. Seguretat i Validació

### 7.1. Validació Centralitzada
- Crear un mòdul de validació reutilitzable
- Validar totes les dades d'entrada

### 7.2. Prepared Statements
- Ja s'està fent bé (ús de ?), continuar amb això
- Mai concatenar strings per a SQL

### 7.3. Rate Limiting
- Limitar peticions per IP per evitar abús
- Especialment per a operacions de carretó

## 8. Monitoring i Logging

### 8.1. Logging Estructurat
- Logs per a operacions importants
- Nivells de log apropiats (DEBUG, INFO, WARNING, ERROR)

### 8.2. Mètriques de Rendiment
- Temps de resposta de consultes
- Nombre de consultes per petició
- Ús de memòria

## 9. Testing i Qualitat

### 9.1. Mocks per a Repositoris
- Amb el patró repositori, és fàcil crear mocks
- Tests unitaris sense dependència de base de dades

### 9.2. Tests d'Integració
- Tests amb base de dades real (SQLite en memòria)
- Validar el comportament complet del sistema

## 10. Escalabilitat Futura

### 10.1. Separació de Lectura/Escriptura
- Lectura: Base de dades replica
- Escriptura: Base de dades principal

### 10.2. Message Queue per Operacions Asíncrones
- Processar comandes de forma asíncrona
- Enviar emails de confirmació en background

### 10.3. CDN per Assets Estàtics
- Servir CSS/JS des d'un CDN
- Millorar temps de càrrega

## Priorització d'Implementació

### Alta Prioritat (Impacte Alt, Esforç Mitjà)
1. ✅ Consulta optimitzada del carretó (get_by_ids)
2. ✅ Patró repositori per productes
3. ✅ Validació de stock en temps real al carretó

### Mitjana Prioritat (Impacte Mitjà, Esforç Baix)
4. Caché simple de productes
5. Índexs de base de dades
6. Logging estructurat

### Baixa Prioritat (Impacte Mitjà, Esforç Alt)
7. Carretó persistit
8. Caché de recomanacions
9. Message queue

## Exemples d'Implementació

Veure els fitxers d'exemple a:
- `repositories/base_repository.py` - Repositori base
- `repositories/product_repository.py` - Repositori de productes
- `services/cart_service.py` - Servei optimitzat de carretó

