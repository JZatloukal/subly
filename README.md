

# 📊 Subly – Chytrý správce předplatného

**Subly** je moderní webová aplikace pro přehlednou správu všech předplatných na jednom místě. Umožňuje sledovat aktivní služby, náklady, frekvenci plateb a upozornění na blížící se platby. Aplikace je navržena tak, aby uživatel snadno získal kontrolu nad svými výdaji.

---

## ⚙️ Technologie

- 🐍 Python (Flask)
- 🗃 SQLite (SQLAlchemy)
- 🎨 HTML, CSS (vlastní styl)
- 📄 Jinja2 šablony
- ✅ Formuláře s CSRF ochranou
- 📦 Bootstrap-like prvky (ručně stylované)
- 💾 Ukládání a mazání předplatných
- 📅 Výpočet dalších plateb podle cyklu (měsíční/roční)

---

## 💡 Funkce

- Přehledný dashboard s kategoriemi předplatného
- Automatický výpočet nadcházející platby
- Vizuální upozornění na blížící se platby
- Přidávání, úprava a mazání předplatných
- Jednotný design a vlastní styl
- Animace pro flash zprávy (např. potvrzení přidání)
- Přihlášení / Registrace uživatele

---

## 🔐 Uživatelské účty

- Ochrana pomocí hesla (uloženého hashovaně)
- Session-based přihlášení
- Flash zprávy s animovaným zmizením
- Login, logout, registrace
- Stránka profilu s možností editace profilu
- (Plánováno) Možnost smazání účtu
- (Plánováno) Obnova zapomenutého hesla

---

## 📷 Ukázky obrazovek

| Přihlášení | Dashboard | Přidání předplatného |
|-----------|-----------|-----------------------|
| ![](screenshots/login.png) | ![](screenshots/dashboard.png) | ![](screenshots/add_subscription.png) |

---

## 🚀 Plánované funkce

- Notifikace na trial verze
- Dark mode (s možností přepnutí)
- Chytré návrhy alternativ (např. levnější varianty)
- Možnost změny měny (CZK, EUR, USD...)
- Timeline plateb (grafické znázornění historie)
- Statistiky výdajů podle kategorií
- Připojení kalendářových notifikací (např. Google Calendar API)
- Automatické ikonky podle služby (Netflix, Spotify, atd.) – částečně hotovo (24 ikon)
- PWA / mobilní aplikace (React Native nebo Swift)
- Sdílení předplatného mezi více uživateli (rodinný režim)
- Lokalizace do angličtiny (i18n)

---

## 🛣 Roadmapa vývoje

- [x] Základní MVP s přidáváním a mazáním předplatných
- [x] Automatický výpočet další platby
- [x] Přehledová stránka s kategoriemi a platbami
- [x] Login/Registrace s ochranou
- [x] Vizuálně jednotný a moderní styl
- [x] Detekce duplicitních služeb (např. dvě stejná předplatná)
- [x] Export dat do CSV / PDF
- [x] Vyhledávání a filtrování předplatných
- [ ] Možnost smazání účtu
- [ ] Obnova zapomenutého hesla
- [ ] Statistiky a přehledy výdajů
- [ ] Nasazení na veřejný hosting

---

## 🛠 Lokální spuštění

```bash
git clone https://github.com/tvoje-jmeno/subly.git
cd subly
python -m venv venv
source venv/bin/activate  # nebo venv\Scripts\activate na Windows
pip install -r requirements.txt
python app.py
```