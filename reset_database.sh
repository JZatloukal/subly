#!/bin/bash

# 🗑️  KOMPLETNÍ RESET DATABÁZE PRO SUBLY
# Tento script kompletně vymaže databázi a restartuje celý proces

echo "🗑️  MAZÁNÍ DATABÁZE A RESTART PROCESU"
echo "======================================"
echo ""

# Přejdi do subly adresáře
cd subly

# 1️⃣ Zastavení aplikace (pokud běží)
echo "1️⃣ Zastavení aplikace (pokud běží)..."
pkill -f "flask run" 2>/dev/null || echo "   Aplikace nebyla spuštěna"
pkill -f "python.*app.py" 2>/dev/null || echo "   Aplikace nebyla spuštěna"
echo ""

# 2️⃣ Mazání databázových souborů
echo "2️⃣ Mazání databázových souborů..."
rm -f instance/database.db
rm -f instance/dev_database.db
echo "   ✅ Databázové soubory smazány"
echo ""

# 3️⃣ Mazání celého migrations adresáře
echo "3️⃣ Mazání celého migrations adresáře..."
rm -rf migrations
echo "   ✅ Migrations adresář smazán"
echo ""

# 4️⃣ Mazání cache souborů
echo "4️⃣ Mazání cache souborů..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Cache soubory smazány"
echo ""

# 5️⃣ Re-inicializace databáze
echo "5️⃣ Re-inicializace databáze..."
flask db init
echo "   ✅ Databáze inicializována"
echo ""

# 6️⃣ Vytvoření první migrace
echo "6️⃣ Vytvoření první migrace..."
flask db migrate -m "Initial migration"
echo "   ✅ Migrace vytvořena"
echo ""

# 7️⃣ Aplikování migrace
echo "7️⃣ Aplikování migrace..."
flask db upgrade
echo "   ✅ Migrace aplikována"
echo ""

# 8️⃣ Ověření stavu
echo "8️⃣ Ověření stavu databáze..."
ls -la instance/
echo ""

echo "🎉 DATABÁZE BYLA KOMPLETNĚ VYMAZÁNA A RESTARTOVÁNA!"
echo ""
echo "📋 Další kroky:"
echo "   • Spusť aplikaci: ./start.sh"
echo "   • Nebo manuálně: flask run"
echo "   • Otevři: http://localhost:5000"
echo ""
echo "💡 Tip: Pro rychlý restart použij: ./reset_database.sh && ./start.sh"