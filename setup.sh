#!/bin/bash

# TechShop - Script d'instal·lació
echo "=== TechShop - Instal·lació ==="
echo ""

# Comprovar si estem en un entorn virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creant entorn virtual..."
    python3 -m venv venv
    echo "Activant entorn virtual..."
    source venv/bin/activate
fi

# Instal·lar dependències
echo "Instal·lant dependències..."
pip install -r requirements.txt

# Inicialitzar la base de dades
echo "Inicialitzant la base de dades..."
cd back-end/database
python3 init_db.py
cd ../..

echo ""
echo "=== Instal·lació completada! ==="
echo ""
echo "Per executar l'aplicació:"
echo "1. Activeu l'entorn virtual: source venv/bin/activate"
echo "2. Executeu: cd back-end && python3 app.py"
echo "3. Obriu el navegador a: http://localhost:5001"

