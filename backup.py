import os
import shutil
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "qarz_daftar.db")
BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID", "")

async def create_backup(bot) -> bool:
    """Ma'lumotlar bazasini backup qilish va Telegram kanalga yuborish"""
    try:
        if not os.path.exists(DB_PATH):
            return False

        # Backup fayl nomi
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_filename = f"backup_{now}.db"
        backup_path = f"/tmp/{backup_filename}"

        # Nusxa olish
        shutil.copy2(DB_PATH, backup_path)

        # Telegram kanalga yuborish
        if BACKUP_CHANNEL_ID:
            with open(backup_path, 'rb') as f:
                await bot.send_document(
                    chat_id=BACKUP_CHANNEL_ID,
                    document=f,
                    filename=backup_filename,
                    caption=f"💾 Avtomatik backup\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )

        # Admins ga ham xabar
        admin_ids = os.getenv("ADMIN_IDS", "")
        if admin_ids:
            for admin_id in admin_ids.split(","):
                try:
                    await bot.send_message(
                        chat_id=int(admin_id.strip()),
                        text=f"✅ Kunlik backup saqlandi!\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                except:
                    pass

        # Temp faylni o'chirish
        os.remove(backup_path)
        return True

    except Exception as e:
        print(f"Backup xatosi: {e}")
        return False
