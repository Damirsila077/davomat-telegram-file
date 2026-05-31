# 📋 Davomat Boshqaruv Boti

Telegram orqali xodimlar davomatini boshqarish tizimi.

---

## 🚀 O'rnatish va Ishga Tushirish

### 1-qadam: Bot Token olish
1. Telegramda **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting (masalan: `MyOfficeBot`)
4. Username kiriting (masalan: `myoffice_attendance_bot`)
5. **Token** ni nusxalab oling

---

### 2-qadam: O'z User ID ingizni bilish
1. Telegramda **@userinfobot** ga yozing
2. `/start` yuboring
3. **Id** raqamini nusxalab oling

---

### 3-qadam: Railway.app da Deploy qilish

1. **https://railway.app** ga boring
2. GitHub bilan ro'yxatdan o'ting
3. **New Project** → **Deploy from GitHub repo**
4. Bu papkani GitHub ga yuklang va tanlang
5. **Add PostgreSQL** → PostgreSQL plugin qo'shing
6. **Variables** bo'limiga quyidagilarni qo'shing:

```
BOT_TOKEN = sizning_bot_tokeningiz
ADMIN_IDS = sizning_user_id_ingiz
DATABASE_URL = (Railway avtomatik beradi - PostgreSQL dan copy qiling)
```

7. **Deploy** tugmasini bosing ✅

---

### 4-qadam: Ofis akkauntini qo'shish
1. Botga `/start` yozing (admin sifatida)
2. **🔐 Ruxsat etilgan akkauntlar** → **➕ Akkaunt qo'shish**
3. Ofis Telegram akkauntining username ini kiriting (masalan: `@office_tashkent`)

---

### 5-qadam: Xodim qo'shish
1. **👥 Xodimlar** → **➕ Xodim qo'shish**
2. ID, ism va PIN kiriting

---

## 📱 Foydalanish

### Ofis telefoni (xodimlar uchun):
| Tugma | Vazifa |
|-------|--------|
| 🟢 Ishni boshlash | Kelish vaqtini qayd etish |
| 🔴 Ishni yakunlash | Ketish vaqtini qayd etish |
| 📊 Mening ma'lumotlarim | O'z davomatini ko'rish (PIN kerak) |

### Admin (siz) uchun:
| Tugma | Vazifa |
|-------|--------|
| 👥 Xodimlar | Xodim qo'shish/tahrirlash/o'chirish |
| 📋 Hisobotlar | Bugungi va oylik hisobotlar |
| ✏️ Davomat tahrirlash | Vaqtni qo'lda o'zgartirish |
| 📁 Excel export | .xlsx fayl eksport |
| 🔐 Ruxsat etilgan akkauntlar | Ofis akkauntlarini boshqarish |
| 📜 Audit log | Barcha o'zgarishlar tarixi |

---

## 🗂 Loyiha Strukturasi

```
attendance_bot/
├── main.py                  # Asosiy fayl
├── requirements.txt         # Kutubxonalar
├── .env.example             # Environment variables namunasi
├── bot/
│   ├── handlers/
│   │   ├── admin.py         # Admin paneli
│   │   └── office.py        # Clock in/out
│   ├── middlewares/
│   │   └── auth.py          # Ruxsatni tekshirish
│   └── keyboards/
│       └── keyboards.py     # Tugmalar
├── repositories/
│   ├── employee_repo.py     # Xodimlar DB
│   ├── attendance_repo.py   # Davomat DB
│   └── other_repos.py      # Boshqa DB
├── models/
│   └── database.py          # Jadval yaratish
└── utils/
    └── excel_export.py      # Excel export
```
