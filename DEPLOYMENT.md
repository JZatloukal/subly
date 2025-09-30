# 🚀 Subly - Deployment Guide

## Railway Deployment

### 1. Příprava projektu

Projekt je připraven pro deployment na Railway s PostgreSQL databází.

### 2. Environment Variables

Nastavte následující environment variables v Railway:

#### Povinné:
- `SECRET_KEY` - Silný secret key pro Flask (vygenerujte náhodný)
- `FLASK_ENV=postgresql` - Konfigurace pro PostgreSQL
- `DATABASE_URL` - Automaticky poskytuje Railway (PostgreSQL connection string)

#### Volitelné:
- `MAIL_SERVER` - SMTP server pro e-maily
- `MAIL_PORT` - Port SMTP serveru
- `MAIL_USE_TLS` - Použít TLS (true/false)
- `MAIL_USERNAME` - E-mail pro odesílání
- `MAIL_PASSWORD` - Heslo pro e-mail

### 3. Railway Setup

1. **Připojte GitHub repository** k Railway
2. **Přidejte PostgreSQL databázi** v Railway dashboard
3. **Nastavte environment variables**:
   ```
   SECRET_KEY=your-super-secret-key-here
   FLASK_ENV=postgresql
   ```
4. **Deploy** - Railway automaticky:
   - Nainstaluje dependencies z `requirements.txt`
   - Spustí migrace
   - Spustí aplikaci s Gunicorn

### 4. Lokální testování s PostgreSQL

Pro testování s PostgreSQL lokálně:

```bash
# Instalace PostgreSQL
brew install postgresql  # macOS
sudo apt-get install postgresql  # Ubuntu

# Spuštění PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Ubuntu

# Vytvoření databáze
createdb subly

# Nastavení environment variables
export DATABASE_URL="postgresql://username:password@localhost:5432/subly"
export FLASK_ENV="postgresql"
export SECRET_KEY="your-secret-key"

# Spuštění aplikace
./start.sh
```

### 5. Migrace

Aplikace automaticky spustí migrace při prvním spuštění:

```bash
flask db upgrade
```

### 6. Monitoring

Railway poskytuje:
- **Logs** - Real-time logy aplikace
- **Metrics** - CPU, RAM, Network usage
- **Database** - PostgreSQL metrics
- **Deployments** - Historie deploymentů

### 7. Troubleshooting

#### Časté problémy:

1. **Database connection error**:
   - Zkontrolujte `DATABASE_URL`
   - Ověřte, že PostgreSQL service běží

2. **Secret key error**:
   - Nastavte `SECRET_KEY` environment variable

3. **Migration error**:
   - Zkontrolujte databázové oprávnění
   - Spusťte `flask db upgrade` manuálně

4. **Port error**:
   - Railway automaticky nastaví `PORT` environment variable
   - Aplikace používá `$PORT` pro binding

### 8. Production Checklist

- [ ] `SECRET_KEY` je nastaven a silný
- [ ] `FLASK_ENV=postgresql` je nastaven
- [ ] PostgreSQL databáze je připojená
- [ ] Migrace proběhly úspěšně
- [ ] Aplikace se spouští bez chyb
- [ ] HTTPS je aktivní (Railway default)
- [ ] Logy nevykazují chyby

### 9. Backup

Railway automaticky zálohuje PostgreSQL databázi. Pro manuální backup:

```bash
pg_dump $DATABASE_URL > backup.sql
```

### 10. Scaling

Railway umožňuje:
- **Horizontal scaling** - Více instancí
- **Vertical scaling** - Více CPU/RAM
- **Auto-scaling** - Automatické škálování podle load

---

## 🎯 Ready for Production!

Aplikace je připravena pro production deployment na Railway s PostgreSQL databází.
