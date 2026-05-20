# 🚌 Mahalla Damas Bot

Mahallaga qatnayotgan damas haydovchilari uchun Telegram bot.

## 📁 Loyiha tuzilmasi

```
mahalla_bot/
├── bot/
│   ├── handlers/
│   │   ├── __init__.py    # Handlerlarni birlashtiradi
│   │   ├── start.py       # /start buyrug'i
│   │   ├── admin.py       # /admin buyrug'i + elon
│   │   └── driver.py      # /driver buyrug'i + ro'yxat
│   ├── bot.py             # Asosiy kirish nuqtasi
│   ├── config.py          # ENV konfiguratsiya
│   ├── api_client.py      # Django backend API
│   ├── keyboards.py       # Barcha tugmalar
│   ├── middlewares.py     # is_admin / is_approved_driver
│   ├── scheduler.py       # 05:00 va 05:15 avtomatik xabarlar
│   └── Dockerfile
├── backend/
│   ├── core/              # Django settings, urls, auth
│   ├── apps/drivers/      # Haydovchilar + DailyStatus
│   ├── apps/users/        # BotUser (elon uchun chat_id lar)
│   ├── apps/announcements/
│   ├── entrypoint.sh      # Migrate + superuser yaratadi
│   └── Dockerfile
├── docker-compose.yml     # Nginx YO'Q - gunicorn :8000 da to'g'ridan-to'g'ri
└── .env.example
```

## 🚀 Serverga deploy qilish

### 1. Fayllarni serverga ko'chiring

```bash
scp -r mahalla_bot/ user@YOUR_SERVER_IP:/home/user/
ssh user@YOUR_SERVER_IP
cd mahalla_bot
```

### 2. `.env` yarating

```bash
cp .env.example .env
nano .env
```

Majburiy to'ldirilishi kerak bo'lgan maydonlar:

```env
BOT_TOKEN=7123456789:AAF...          # @BotFather dan
GROUP_CHAT_ID=-1001234567890         # Guruh chat ID (bot admin bo'lishi kerak)
ADMIN_IDS=123456789                  # Sizning Telegram ID ingiz

DJANGO_SECRET_KEY=...                # openssl rand -hex 32
POSTGRES_PASSWORD=strong_pass        # Xavfsiz parol
BACKEND_API_KEY=random-secret        # openssl rand -hex 16

DJANGO_SUPERUSER_PASSWORD=admin123   # Django admin paroli
```

### 3. Ishga tushirish

```bash
docker-compose up -d --build
```

### 4. Tekshirish

```bash
# Barcha konteynerlar
docker-compose ps

# Backend ishlayaptimi?
curl http://localhost:8000/admin/

# Loglar
docker-compose logs -f bot
docker-compose logs -f backend
```

### 5. Django Admin

```
http://YOUR_SERVER_IP:8000/admin/
```
Login: `.env` dagi `DJANGO_SUPERUSER_USERNAME` va `DJANGO_SUPERUSER_PASSWORD`

---

## 🌐 Port

| Servis | Port | Tavsif |
|--------|------|--------|
| Backend (gunicorn) | **8000** | To'g'ridan-to'g'ri ochiq |
| PostgreSQL | 5432 | Faqat ichki (tashqariga yopiq) |

> Nginx ishlatilmaydi. Gunicorn `0.0.0.0:8000` da ishlaydi, `whitenoise` orqali static fayllar ham serve qilinadi.

---

## ⏰ Avtomatik vazifalar (scheduler)

| Vaqt | Vazifa |
|------|--------|
| **05:00** | Barcha haydovchilarga "Bugun ishga chiqasizmi?" |
| **05:15** | Bugungi ishlaydigan haydovchilar ro'yxatini guruhga yuborish |

---

## 🤖 Bot buyruqlari

| Buyruq | Kim uchun | Tavsif |
|--------|-----------|--------|
| `/start` | Hammaga | Asosiy menyu, ro'yxatga olish |
| `/admin` | Adminlar | Admin panel (ADMIN_IDS tekshiriladi) |
| `/driver` | Haydovchilar | Haydovchi panel (DB tekshiriladi) |

---

## 🔧 Foydali buyruqlar

```bash
# To'xtatish
docker-compose down

# Qayta ishga tushirish
docker-compose restart bot

# Yangilanish (kod o'zgarganda)
docker-compose down
docker-compose up -d --build

# DB backup
docker exec mahalla_db pg_dump -U mahalla_user mahalla_bot > backup.sql
```
git cache tozalash
git rm -r --cached .
