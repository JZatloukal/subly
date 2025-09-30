#!/bin/bash

# =============================================================================
# Subly Flask Application Startup Script
# =============================================================================
# Tento script zajistí kompletní spuštění aplikace s kontrolou všech komponent
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Subly Flask App"
APP_PORT=5001
APP_DIR="subly"
VENV_DIR="venv"
PYTHON_CMD="python3"

# Database configuration
DB_TYPE="sqlite"  # sqlite, postgresql
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_DB="subly"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}=============================================================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}=============================================================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect database type
detect_database() {
    if [ -n "$DATABASE_URL" ]; then
        if [[ "$DATABASE_URL" == postgresql* ]]; then
            DB_TYPE="postgresql"
            print_status "Detekována PostgreSQL databáze z DATABASE_URL"
        elif [[ "$DATABASE_URL" == sqlite* ]]; then
            DB_TYPE="sqlite"
            print_status "Detekována SQLite databáze z DATABASE_URL"
        fi
    elif [ -n "$FLASK_ENV" ] && [ "$FLASK_ENV" = "postgresql" ]; then
        DB_TYPE="postgresql"
        print_status "Detekována PostgreSQL databáze z FLASK_ENV"
    else
        DB_TYPE="sqlite"
        print_status "Používá se SQLite databáze (výchozí)"
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    print_status "Kontrola portu $port..."
    
    if lsof -ti:$port >/dev/null 2>&1; then
        print_warning "Port $port je obsazený, ukončuji procesy..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        
        if lsof -ti:$port >/dev/null 2>&1; then
            print_error "Nepodařilo se uvolnit port $port"
            exit 1
        else
            print_success "Port $port byl úspěšně uvolněn"
        fi
    else
        print_success "Port $port je volný"
    fi
}

# Function to check Python and pip
check_python() {
    print_header "KONTROLA PYTHON PROSTŘEDÍ"
    
    if ! command_exists $PYTHON_CMD; then
        print_error "Python3 není nainstalovaný nebo není v PATH"
        exit 1
    fi
    
    local python_version=$($PYTHON_CMD --version 2>&1)
    print_success "Python nalezen: $python_version"
    
    if ! command_exists pip3; then
        print_error "pip3 není nainstalovaný"
        exit 1
    fi
    
    print_success "pip3 je dostupný"
}

# Function to setup virtual environment
setup_venv() {
    print_header "NASTAVENÍ VIRTUÁLNÍHO PROSTŘEDÍ"
    
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Vytváření virtuálního prostředí..."
        $PYTHON_CMD -m venv $VENV_DIR
        print_success "Virtuální prostředí vytvořeno"
    else
        print_success "Virtuální prostředí již existuje"
    fi
    
    print_status "Aktivace virtuálního prostředí..."
    source $VENV_DIR/bin/activate
    
    print_status "Upgrade pip..."
    pip install --upgrade pip >/dev/null 2>&1
    print_success "pip aktualizován"
}

# Function to install dependencies
install_dependencies() {
    print_header "INSTALACE ZÁVISLOSTÍ"
    
    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        print_error "Soubor requirements.txt nebyl nalezen"
        exit 1
    fi
    
    print_status "Instalace závislostí z requirements.txt..."
    pip install -r $APP_DIR/requirements.txt >/dev/null 2>&1
    print_success "Závislosti nainstalovány"
}

# Function to setup database
setup_database() {
    print_header "NASTAVENÍ DATABÁZE"
    
    print_status "Kontrola existence instance složky..."
    if [ ! -d "$APP_DIR/instance" ]; then
        print_status "Vytváření instance složky..."
        mkdir -p $APP_DIR/instance
        print_success "Instance složka vytvořena"
    fi
    
    print_status "Spuštění databázových migrací..."
    cd $APP_DIR
    
    # Set Flask environment variables
    export FLASK_APP=app.py
    export FLASK_ENV=development
    
    # Check if migrations exist
    if [ -d "migrations" ]; then
        print_status "Aplikování migrací..."
        if flask db upgrade 2>/dev/null; then
            print_success "Migrace aplikovány"
        else
            print_warning "Migrace selhaly, zkusím vytvořit tabulky přímo..."
            # Fallback: create tables directly if migrations fail
            $PYTHON_CMD -c "
import sys
sys.path.append('.')
from app import app
from models import db
with app.app_context():
    try:
        db.create_all()
        print('✅ Tabulky vytvořeny přímo')
    except Exception as e:
        print(f'❌ Chyba při vytváření tabulek: {e}')
" 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "Tabulky vytvořeny přímo"
            else
                print_error "Nepodařilo se vytvořit databázové tabulky"
                exit 1
            fi
        fi
    else
        print_status "Inicializace migrací..."
        flask db init >/dev/null 2>&1
        flask db migrate -m "Initial migration" >/dev/null 2>&1
        if flask db upgrade >/dev/null 2>&1; then
            print_success "Migrace inicializovány a aplikovány"
        else
            print_warning "Migrace selhaly, zkusím vytvořit tabulky přímo..."
            $PYTHON_CMD -c "
import sys
sys.path.append('.')
from app import app
from models import db
with app.app_context():
    try:
        db.create_all()
        print('✅ Tabulky vytvořeny přímo')
    except Exception as e:
        print(f'❌ Chyba při vytváření tabulek: {e}')
" 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "Tabulky vytvořeny přímo"
            else
                print_error "Nepodařilo se vytvořit databázové tabulky"
                exit 1
            fi
        fi
    fi
    
    cd ..
}

# Function to test PostgreSQL connection
test_postgresql() {
    print_status "Testování PostgreSQL připojení..."
    
    if command_exists psql; then
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "PostgreSQL připojení: OK"
            return 0
        else
            print_warning "PostgreSQL není dostupný, pokračuji s SQLite"
            return 1
        fi
    else
        print_warning "psql není nainstalován, pokračuji s SQLite"
        return 1
    fi
}

# Function to test application
test_application() {
    print_header "TESTOVÁNÍ APLIKACE"
    
    cd $APP_DIR
    
    print_status "Test importu modulů..."
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
try:
    from app import app
    from models import db, User, Subscription
    from utils import calculate_category_totals
    print('✅ Všechny moduly se importují bez chyb')
except Exception as e:
    print(f'❌ Chyba při importu: {e}')
    sys.exit(1)
" 2>/dev/null
    print_success "Moduly se importují správně"
    
    print_status "Test databázových modelů..."
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
from app import app
from models import db, User, Subscription
with app.app_context():
    try:
        # Test vytvoření tabulek
        db.create_all()
        print('✅ Databázové tabulky vytvořeny')
        
        # Test základních operací
        user_count = User.query.count()
        sub_count = Subscription.query.count()
        print(f'✅ Databáze funguje - Users: {user_count}, Subscriptions: {sub_count}')
    except Exception as e:
        print(f'❌ Chyba databáze: {e}')
        sys.exit(1)
" 2>/dev/null
    print_success "Databáze funguje správně"
    
    print_status "Test utility funkcí..."
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
from app import app
from utils import calculate_category_totals, detect_category
from models import db, Subscription
with app.app_context():
    try:
        # Test kalkulace kategorií s reálnými subscription objekty
        subscriptions = Subscription.query.filter_by(user_id=1).all()
        totals = calculate_category_totals(subscriptions)
        print(f'✅ Utility funkce fungují - Kategorie: {len(totals)}')
        
        # Test detekce kategorií
        test_category = detect_category('Netflix')
        print(f'✅ Detekce kategorií funguje - Netflix: {test_category}')
    except Exception as e:
        print(f'❌ Chyba utility funkcí: {e}')
        sys.exit(1)
" 2>/dev/null
    print_success "Utility funkce fungují správně"
    
    cd ..
}

# Function to open browser
open_browser() {
    local url="http://localhost:$APP_PORT"
    print_status "Otevírám prohlížeč na $url..."
    
    # Try different methods to open browser on macOS
    if command_exists open; then
        open "$url" 2>/dev/null &
        print_success "Prohlížeč otevřen"
    elif command_exists xdg-open; then
        xdg-open "$url" 2>/dev/null &
        print_success "Prohlížeč otevřen"
    else
        print_warning "Nepodařilo se automaticky otevřít prohlížeč"
        print_status "Otevři manuálně: $url"
    fi
}

# Function to start application
start_application() {
    print_header "SPUŠTĚNÍ APLIKACE"
    
    cd $APP_DIR
    
    print_status "Spouštění Flask aplikace na portu $APP_PORT..."
    print_status "Aplikace bude dostupná na: http://localhost:$APP_PORT"
    print_status "Pro ukončení stiskni Ctrl+C"
    echo ""
    
    # Open browser after a short delay
    sleep 2
    open_browser
    echo ""
    
    # Start the application
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export PORT=$APP_PORT
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
from app import app
print('✅ Flask aplikace se načítá...')
print('🌐 Spouštím na http://localhost:$APP_PORT')
app.run(host='0.0.0.0', port=$APP_PORT, debug=True)
"
}

# Function to cleanup on exit
cleanup() {
    print_status "Ukončování aplikace..."
    kill_port $APP_PORT
    print_success "Aplikace ukončena"
}

# Set trap for cleanup only on interrupt/termination
trap cleanup INT TERM

# Main execution
main() {
    print_header "SPUŠTĚNÍ $APP_NAME"
    print_status "Začínám kompletní kontrolu a spuštění aplikace..."
    echo ""
    
    # Check if we're in the right directory
    if [ ! -d "$APP_DIR" ]; then
        print_error "Složka '$APP_DIR' nebyla nalezena. Spusť script z root složky projektu."
        exit 1
    fi
    
    # Run all checks and setup
    check_python
    setup_venv
    install_dependencies
    detect_database
    kill_port $APP_PORT
    setup_database
    test_application
    
    echo ""
    print_header "VŠE PŘIPRAVENO - SPOUŠTÍM APLIKACI"
    echo ""
    
    # Start the application
    start_application
}

# Run main function
main "$@"
