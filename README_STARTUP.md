# 🚀 Subly Flask - Startovací Scripty

## Přehled

Tento projekt obsahuje kompletní startovací scripty, které zajistí bezchybné spuštění aplikace s kontrolou všech komponent.

## 📁 Soubory

- **`start.sh`** - Startovací script pro macOS/Linux
- **`README_STARTUP.md`** - Tato dokumentace

## 🎯 Co scripty dělají

### 1. **Kontrola prostředí**
- ✅ Kontrola Python3 a pip
- ✅ Kontrola existence virtuálního prostředí
- ✅ Vytvoření venv pokud neexistuje

### 2. **Instalace závislostí**
- ✅ Aktivace virtuálního prostředí
- ✅ Upgrade pip na nejnovější verzi
- ✅ Instalace všech závislostí z `requirements.txt`

### 3. **Kontrola portu**
- ✅ Kontrola obsazení portu 2000
- ✅ Automatické ukončení konfliktních procesů
- ✅ Uvolnění portu pro aplikaci

### 4. **Databáze a migrace**
- ✅ Vytvoření instance složky
- ✅ Inicializace Flask-Migrate (pokud neexistuje)
- ✅ Aplikování všech databázových migrací
- ✅ Vytvoření databázových tabulek

### 5. **Testování aplikace**
- ✅ Test importu všech modulů
- ✅ Test databázových modelů
- ✅ Test utility funkcí
- ✅ Kontrola funkčnosti kalkulací

### 6. **Spuštění aplikace**
- ✅ Spuštění Flask aplikace na portu 2000
- ✅ Barevný výstup s informacemi o stavu
- ✅ Automatické ukončení při Ctrl+C

## 🖥️ Použití

### macOS/Linux
```bash
# Spuštění scriptu
./start.sh

# Nebo s bash
bash start.sh
```

## 📊 Výstup scriptu

Script poskytuje barevný výstup s informacemi o:

- 🔵 **[INFO]** - Informační zprávy
- 🟢 **[SUCCESS]** - Úspěšné operace
- 🟡 **[WARNING]** - Varování
- 🔴 **[ERROR]** - Chyby

### Příklad výstupu:
```
=============================================================================
 SPUŠTĚNÍ Subly Flask App
=============================================================================
[INFO] Začínám kompletní kontrolu a spuštění aplikace...

=============================================================================
 KONTROLA PYTHON PROSTŘEDÍ
=============================================================================
[SUCCESS] Python nalezen: Python 3.13.0
[SUCCESS] pip3 je dostupný

=============================================================================
 NASTAVENÍ VIRTUÁLNÍHO PROSTŘEDÍ
=============================================================================
[SUCCESS] Virtuální prostředí již existuje
[SUCCESS] pip aktualizován

=============================================================================
 INSTALACE ZÁVISLOSTÍ
=============================================================================
[SUCCESS] Závislosti nainstalovány

=============================================================================
 NASTAVENÍ DATABÁZE
=============================================================================
[SUCCESS] Migrace aplikovány

=============================================================================
 TESTOVÁNÍ APLIKACE
=============================================================================
[SUCCESS] Moduly se importují správně
[SUCCESS] Databáze funguje správně
[SUCCESS] Utility funkce fungují správně

=============================================================================
 VŠE PŘIPRAVENO - SPOUŠTÍM APLIKACI
=============================================================================
[INFO] Spouštění Flask aplikace na portu 2000...
[INFO] Aplikace bude dostupná na: http://localhost:2000
```

## 🛠️ Řešení problémů

### Port je obsazený
Script automaticky ukončí procesy na portu 2000. Pokud to nefunguje:
```bash
# Ruční ukončení
lsof -ti:2000 | xargs kill -9
```

### Chyby s Python
Ujistěte se, že máte nainstalovaný Python 3.8+:
```bash
python3 --version
```

### Chyby s virtuálním prostředím
Script automaticky vytvoří venv, ale můžete ho vytvořit ručně:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r subly/requirements.txt
```

### Chyby s databází
Script automaticky spustí migrace, ale můžete je spustit ručně:
```bash
cd subly
flask db upgrade
```

## 🔧 Konfigurace

Můžete upravit konfiguraci v scriptu:

```bash
# Port aplikace
APP_PORT=2000

# Složka s aplikací
APP_DIR="subly"

# Složka s venv
VENV_DIR="venv"

# Python příkaz
PYTHON_CMD="python3"
```

## 📝 Poznámky

- Script automaticky detekuje a řeší většinu běžných problémů
- Všechny operace jsou logovány s barevným výstupem
- Script se ukončí při jakékoliv chybě (fail-fast)
- Automatické cleanup při ukončení (Ctrl+C)

## 🎉 Výsledek

Po úspěšném spuštění uvidíte:
- ✅ Všechny kontroly prošly bez chyb
- ✅ Aplikace běží na http://localhost:2000
- ✅ Databáze je připravena a funkční
- ✅ Všechny moduly a funkce fungují správně
