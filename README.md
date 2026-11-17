# ⚡ HH Parser Pro – HeadHunter Vacancy Intelligence Dashboard

Zamonaviy, tezkor va professional [hh.uz](https://hh.uz) (HeadHunter) vakansiyalarini tahlil qilish, qidirish va eksport qilish tizimi. 
Loyiha zamonaviy Web UI (Dark Theme), to'liq Docker qo'llab-quvvatlashi va bir nechta formatlarda (Excel, CSV, JSON) eksport qilish imkoniyatiga ega.

---

## ✨ Imkoniyatlar va Afzalliklar

* 🚀 **Tezkor va Xavfsiz Parsing**: Eski sekin brauzer (Selenium) o'rniga, to'g'ridan-to'g'ri ochiq ma'lumotlar oqimidan foydalanadi. 40-50 ta vakansiyani 1-2 soniyada yig'adi.
* 🐳 **Docker-Ready**: Bitta `docker run` buyrug'i orqali to'liq izolyatsiyalangan holda ishga tushadi.
* 🎨 **Zamonaviy Web UI (High-Craft)**: Interaktiv qidiruv, real-vaqt filtrlari, saralash, bento-kartochkalar va Chart.js grafiklari.
* 📊 **Analitika va Statistika**:
  - O'rtacha oylik maosh (USD / UZS)
  - Masofaviy (Remote) ishlar foizi
  - Tajriba talablari bo'yicha taqsimot (Doughnut chart)
  - Eng ko'p ish o'rni taklif qilayotgan TOP-5 kompaniyalar (Bar chart)
* 📥 **3 xil Eksport formati**:
  - **CSV (Excel)**: UTF-8 BOM bilan (o'zbek va ruscha harflar Excel da buzilmaydi).
  - **Excel (.xlsx)**: To'liq jadvallashtirilgan fayl.
  - **JSON**: Dasturchilar va API integratsiyasi uchun.
* 🔐 **Hisob va Captcha boshqaruvi**:
  - **Ochiq rejim (Tavsiya etiladi)**: Loginsiz, bot-blokirovkasiz 100% xavfsiz.
  - **Sessiya rejimi**: HH.uz hisob ma'lumotlari yoki cookie sessiyasini kiritish imkoniyati.

---

## 🐳 Docker orqali ishga tushirish (Tavsiya etiladi)

Docker o'rnatilgan bo'lsa (Docker Desktop yoniq bo'lishi kerak):

### 1-usul: Bitta buyruq bilan (docker run)
```bash
# 1. Obrazni qurish
docker build -t hh-parser .

# 2. Konteynerni ishga tushirish
docker run -d -p 8000:8000 --name hh_parser_app hh-parser
```

### 2-usul: Docker Compose orqali
```bash
docker compose up -d --build
```

Konteyner ishga tushgach, brauzeringizda quyidagi manzilni oching:
👉 **[http://localhost:8000](http://localhost:8000)**

Konteynerni to'xtatish uchun:
```bash
docker stop hh_parser_app
```

---

## 💻 Mahalliy (Local) ishga tushirish (Dockersiz)

Agar Docker ishlatmasdan to'g'ridan-to'g'ri Python orqali ishga tushirmoqchi bo'lsangiz:

1. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. Dasturni ishga tushiring:
   ```bash
   python main.py
   ```
   Dastur avtomatik ravishda brauzeringizda **http://localhost:8000** manzilini ochadi.

---

## 🛠️ API Endpoints

| Metod | Endpoint | Tavsif |
|---|---|---|
| `GET` | `/` | Asosiy Web Dashboard (UI) |
| `POST` | `/api/search` | Vakansiyalarni qidirish va filtrlash |
| `GET` | `/api/results` | Oxirgi qidiruv natijalari |
| `GET` | `/api/stats` | Tahliliy statistika va diagramma ma'lumotlari |
| `GET` | `/api/export/csv` | Natijalarni CSV formatida yuklab olish |
| `GET` | `/api/export/excel` | Natijalarni Excel (.xlsx) formatida yuklab olish |
| `GET` | `/api/export/json` | Natijalarni JSON formatida yuklab olish |
| `POST` | `/api/auth/login` | HH.uz sessiyasini saqlash |

---

## 📁 Loyiha Strukturasi

```
hh_parser/
├── app.py              # FastAPI server va REST API yo'nalishlari
├── scraper.py          # HeadHunter zamonaviy parser mexanizmi
├── main.py             # Mahalliy tezkor ishga tushirish skripti
├── Dockerfile          # Docker konteyner konfiguratsiyasi
├── docker-compose.yml  # Docker compose sozlamalari
├── requirements.txt    # Kerakli Python kutubxonalari
├── static/
│   └── index.html      # Zamonaviy High-Craft Web UI (Tailwind + Lucide + Chart.js)
└── README.md           # Hujjatlar
```
