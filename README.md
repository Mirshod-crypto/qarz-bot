# 🏪 Do'kon Qarz Daftari - Telegram Bot

## ✨ Imkoniyatlar
- ➕ Qarz qo'shish va to'lov qabul qilish
- 📊 Har bir mijoz uchun tarix (nima oldi, qachon, qancha)
- 🔄 **Avtomatik lotin ↔ kirill** o'girish
- 👥 4 nafar xodim bir botda ishlay oladi
- ⚠️ Har kuni muddati o'tgan qarzlar uchun eslatma
- 💰 Kirim-chiqim hisobi
- 💾 Har kuni avtomatik backup (Telegram kanalga)
- 🔍 Ism bo'yicha qidirish

---

## 🚀 O'rnatish - 3 QADAM

### 1-QADAM: Bot yaratish
1. Telegramda **@BotFather** ga boring
2. `/newbot` buyrug'ini yuboring
3. Bot uchun nom bering (masalan: `Dokon Qarz Daftari`)
4. Bot uchun username bering (masalan: `dokonim_qarz_bot`)
5. **Bot token** ni nusxa oling (shunday ko'rinadi: `7123456789:AAF...`)

### 2-QADAM: Telegram ID larni bilish
1. **@userinfobot** ga `/start` yuboring
2. U sizning Telegram ID ingizni ko'rsatadi (masalan: `123456789`)
3. Barcha xodimlar ham shu qadamni bajarisin

### 3-QADAM: Railway.app ga joylash (BEPUL, umrbod ishlaydi)

#### a) GitHub ga yuklash:
1. [github.com](https://github.com) da hisob oching
2. Yangi repository yarating: `qarz-bot`
3. Bu papkadagi barcha fayllarni yuklab qo'ying
   - `bot.py`, `database.py`, `transliterate.py`, `backup.py`
   - `requirements.txt`, `Procfile`

#### b) Railway da ishga tushirish:
1. [railway.app](https://railway.app) ga kiring (GitHub bilan)
2. **"New Project"** → **"Deploy from GitHub repo"**
3. `qarz-bot` repository ni tanlang
4. **Variables** bo'limiga o'ting va quyidagilarni qo'shing:

| Variable | Qiymat | Misol |
|----------|--------|-------|
| `BOT_TOKEN` | @BotFather dan olgan token | `7123456789:AAF...` |
| `ADMIN_IDS` | Xodimlar ID lari (vergul bilan) | `123456789,987654321` |
| `BACKUP_CHANNEL_ID` | Backup kanali ID (ixtiyoriy) | `-1001234567890` |

5. **"Deploy"** tugmasini bosing → Tayyor! 🎉

---

## 💾 Backup kanali yaratish (ixtiyoriy, lekin tavsiya etiladi)

1. Telegramda yangi kanal yarating (masalan: `Dokon Backup`)
2. Kanalga botingizni **admin** qilib qo'shing
3. Kanal ID sini bilish: kanal habarini forward qiling **@userinfobot** ga
4. ID (masalan: `-1001234567890`) ni Railway dagi `BACKUP_CHANNEL_ID` ga qo'shing

---

## 📱 Botdan foydalanish

### Qarz qo'shish:
1. `/start` → **➕ Qarz qo'shish**
2. Ismni kiriting: `Doston`
3. Telefon (yoki o'tkazib yuborish)
4. Mahsulot: `Non`
5. Summa: `100000`
6. Muddat: `10` (kun) yoki o'tkazib yuborish

### Qarz ustiga qo'shish:
- Qarzdorni topib oching → **➕ Yana qarz qo'shish**
- Doston 4-kuni kelsa → ustiga qo'shing → jami ko'rsatadi

### To'lov qabul qilish:
- Qarzdorni oching → **💵 To'lov qabul qilish** → summa kiriting
- Avtomatik hisoblab qoldiqni ko'rsatadi

### Eslatmalar:
- Har kuni soat 09:00 da muddati o'tganlarga **avtoeslatma** yuboriladi

---

## 🔄 Lotin ↔ Kirill

- Siz **lotin** da yozsangiz → dadangiz **kirillcha** ko'radi
- Dadangiz **kirillcha** yozsa → siz **lotincha** ko'rasiz
- Sozlamalar → Til tanlang

---

## ❓ Yordam

Muammo bo'lsa, botga `/start` yuboring yoki Railway loglarini tekshiring.
