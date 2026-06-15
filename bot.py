import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from transliterate import uz_to_cyrillic, cyrillic_to_uz
from backup import create_backup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
(MAIN_MENU, ADD_DEBTOR_NAME, ADD_DEBTOR_PHONE, ADD_DEBT_AMOUNT,
 ADD_DEBT_PRODUCT, ADD_DEBT_DAYS, ADD_PAYMENT, SEARCH_DEBTOR,
 INCOME_AMOUNT, INCOME_DESC, EXPENSE_AMOUNT, EXPENSE_DESC,
 CONFIRM_DELETE, SELECT_DEBTOR_FOR_PAYMENT) = range(14)

db = Database()

# Authorized users - BOT_ADMIN_IDS dan olinadi
def get_admins():
    ids = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in ids.split(",") if x.strip()]

def is_authorized(user_id: int) -> bool:
    admins = get_admins()
    if not admins:
        return True  # Hech kim sozlanmagan bo'lsa, hamma kira oladi
    return user_id in admins

def get_user_lang(user_id: int) -> str:
    return db.get_user_lang(user_id)

def translate_text(text: str, target_lang: str) -> str:
    """Matnni target_lang ga o'girish"""
    if target_lang == "cyrillic":
        return uz_to_cyrillic(text)
    else:
        return cyrillic_to_uz(text)

def format_money(amount: float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"

def main_keyboard(lang: str):
    if lang == "cyrillic":
        buttons = [
            [InlineKeyboardButton("➕ Қарз қўшиш", callback_data="add_debt"),
             InlineKeyboardButton("🔍 Қидириш", callback_data="search")],
            [InlineKeyboardButton("📋 Барча қарздорлар", callback_data="all_debtors"),
             InlineKeyboardButton("⚠️ Муддати ўтганлар", callback_data="overdue")],
            [InlineKeyboardButton("💰 Кирим", callback_data="income"),
             InlineKeyboardButton("💸 Чиқим", callback_data="expense")],
            [InlineKeyboardButton("📊 Ҳисобот", callback_data="report"),
             InlineKeyboardButton("⚙️ Созламалар", callback_data="settings")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton("➕ Qarz qo'shish", callback_data="add_debt"),
             InlineKeyboardButton("🔍 Qidirish", callback_data="search")],
            [InlineKeyboardButton("📋 Barcha qarzdorlar", callback_data="all_debtors"),
             InlineKeyboardButton("⚠️ Muddati o'tganlar", callback_data="overdue")],
            [InlineKeyboardButton("💰 Kirim", callback_data="income"),
             InlineKeyboardButton("💸 Chiqim", callback_data="expense")],
            [InlineKeyboardButton("📊 Hisobot", callback_data="report"),
             InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("❌ Sizga ruxsat yo'q. Admin bilan bog'laning.")
        return ConversationHandler.END

    # Yangi foydalanuvchini qo'shish
    db.add_user(user.id, user.first_name, user.username)
    lang = get_user_lang(user.id)

    if lang == "cyrillic":
        text = f"Салом, {user.first_name}! 👋\n\n🏪 <b>Дўкон Қарз Дафтари</b>\n\nНимани қилмоқчисиз?"
    else:
        text = f"Salom, {user.first_name}! 👋\n\n🏪 <b>Do'kon Qarz Daftari</b>\n\nNimani qilmoqchisiz?"

    await update.message.reply_text(text, reply_markup=main_keyboard(lang), parse_mode="HTML")
    return MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_user_lang(user_id)

    if query.data == "main_menu":
        if lang == "cyrillic":
            text = "🏪 <b>Бош меню</b>"
        else:
            text = "🏪 <b>Bosh menyu</b>"
        await query.edit_message_text(text, reply_markup=main_keyboard(lang), parse_mode="HTML")
        return MAIN_MENU

    elif query.data == "add_debt":
        if lang == "cyrillic":
            text = "👤 Қарздорнинг исмини киритинг:"
        else:
            text = "👤 Qarzdorning ismini kiriting:"
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]])
        await query.edit_message_text(text, reply_markup=back_btn)
        context.user_data['action'] = 'add_debtor_name'
        return ADD_DEBTOR_NAME

    elif query.data == "search":
        if lang == "cyrillic":
            text = "🔍 Қидириш учун исм ёки телефон рақамини киритинг:"
        else:
            text = "🔍 Qidirish uchun ism yoki telefon raqamini kiriting:"
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]])
        await query.edit_message_text(text, reply_markup=back_btn)
        context.user_data['action'] = 'search'
        return SEARCH_DEBTOR

    elif query.data == "all_debtors":
        return await show_all_debtors(query, lang)

    elif query.data == "overdue":
        return await show_overdue(query, lang)

    elif query.data == "income":
        if lang == "cyrillic":
            text = "💰 Кирим суммасини киритинг (сўм):"
        else:
            text = "💰 Kirim summasini kiriting (so'm):"
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]])
        await query.edit_message_text(text, reply_markup=back_btn)
        context.user_data['action'] = 'income'
        return INCOME_AMOUNT

    elif query.data == "expense":
        if lang == "cyrillic":
            text = "💸 Чиқим суммасини киритинг (сўм):"
        else:
            text = "💸 Chiqim summasini kiriting (so'm):"
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]])
        await query.edit_message_text(text, reply_markup=back_btn)
        context.user_data['action'] = 'expense'
        return EXPENSE_AMOUNT

    elif query.data == "report":
        return await show_report(query, lang)

    elif query.data == "settings":
        return await show_settings(query, lang)

    elif query.data.startswith("debtor_"):
        debtor_id = int(query.data.split("_")[1])
        return await show_debtor_detail(query, debtor_id, lang)

    elif query.data.startswith("pay_"):
        debtor_id = int(query.data.split("_")[1])
        context.user_data['pay_debtor_id'] = debtor_id
        if lang == "cyrillic":
            text = "💵 Тўлов суммасини киритинг (сўм):"
        else:
            text = "💵 To'lov summasini kiriting (so'm):"
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data=f"debtor_{debtor_id}")]])
        await query.edit_message_text(text, reply_markup=back_btn)
        return ADD_PAYMENT

    elif query.data.startswith("add_more_"):
        debtor_id = int(query.data.split("_")[2])
        context.user_data['existing_debtor_id'] = debtor_id
        if lang == "cyrillic":
            text = "📦 Маҳсулот номини киритинг:"
        else:
            text = "📦 Mahsulot nomini kiriting:"
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data=f"debtor_{debtor_id}")]])
        await query.edit_message_text(text, reply_markup=back_btn)
        context.user_data['action'] = 'add_product'
        return ADD_DEBT_PRODUCT

    elif query.data.startswith("delete_debtor_"):
        debtor_id = int(query.data.split("_")[2])
        debtor = db.get_debtor(debtor_id)
        if lang == "cyrillic":
            text = f"⚠️ <b>{debtor['name']}</b> қарздорини ўчиришни тасдиқлайсизми?\nБарча маълумотлар ўчади!"
            buttons = [
                [InlineKeyboardButton("✅ Ҳа, ўчир", callback_data=f"confirm_delete_{debtor_id}"),
                 InlineKeyboardButton("❌ Йўқ", callback_data=f"debtor_{debtor_id}")]
            ]
        else:
            text = f"⚠️ <b>{debtor['name']}</b> qarzdorini o'chirishni tasdiqlaysizmi?\nBarcha ma'lumotlar o'chadi!"
            buttons = [
                [InlineKeyboardButton("✅ Ha, o'chir", callback_data=f"confirm_delete_{debtor_id}"),
                 InlineKeyboardButton("❌ Yo'q", callback_data=f"debtor_{debtor_id}")]
            ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        return CONFIRM_DELETE

    elif query.data.startswith("confirm_delete_"):
        debtor_id = int(query.data.split("_")[2])
        db.delete_debtor(debtor_id)
        if lang == "cyrillic":
            text = "✅ Қарздор ўчирилди!"
        else:
            text = "✅ Qarzdor o'chirildi!"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        return MAIN_MENU

    elif query.data.startswith("lang_"):
        new_lang = query.data.split("_")[1]
        db.set_user_lang(user_id, new_lang)
        lang = new_lang
        if lang == "cyrillic":
            text = "✅ Тил ўзгартирилди: Кирилл"
        else:
            text = "✅ Til o'zgartirildi: O'zbek lotin"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        return MAIN_MENU

    elif query.data.startswith("backup_now"):
        await query.edit_message_text("⏳ Backup yaratilmoqda...")
        result = await create_backup(context.bot)
        if lang == "cyrillic":
            text = "✅ Backup муваффақиятли яратилди ва Telegram каналга юборилди!"
        else:
            text = "✅ Backup muvaffaqiyatli yaratildi va Telegram kanalga yuborildi!"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        return MAIN_MENU

    return MAIN_MENU

async def show_all_debtors(query, lang):
    debtors = db.get_all_debtors_with_balance()
    if not debtors:
        if lang == "cyrillic":
            text = "📋 Қарздорлар йўқ"
        else:
            text = "📋 Qarzdorlar yo'q"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        return MAIN_MENU

    buttons = []
    for d in debtors:
        name = translate_text(d['name'], lang)
        balance = d['total_debt'] - d['total_paid']
        if balance > 0:
            label = f"🔴 {name} — {format_money(balance)}"
        else:
            label = f"✅ {name} — To'langan"
        buttons.append([InlineKeyboardButton(label, callback_data=f"debtor_{d['id']}")])

    buttons.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")])

    if lang == "cyrillic":
        text = f"📋 <b>Барча қарздорлар ({len(debtors)} та):</b>"
    else:
        text = f"📋 <b>Barcha qarzdorlar ({len(debtors)} ta):</b>"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return MAIN_MENU

async def show_overdue(query, lang):
    debtors = db.get_overdue_debtors()
    if not debtors:
        if lang == "cyrillic":
            text = "✅ Муддати ўтган қарзлар йўқ!"
        else:
            text = "✅ Muddati o'tgan qarzlar yo'q!"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        return MAIN_MENU

    buttons = []
    for d in debtors:
        name = translate_text(d['name'], lang)
        balance = d['total_debt'] - d['total_paid']
        days_over = d['days_overdue']
        label = f"⚠️ {name} — {format_money(balance)} ({days_over} kun)"
        buttons.append([InlineKeyboardButton(label, callback_data=f"debtor_{d['id']}")])

    buttons.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")])

    if lang == "cyrillic":
        text = f"⚠️ <b>Муддати ўтган қарзлар ({len(debtors)} та):</b>"
    else:
        text = f"⚠️ <b>Muddati o'tgan qarzlar ({len(debtors)} ta):</b>"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return MAIN_MENU

async def show_debtor_detail(query, debtor_id, lang):
    debtor = db.get_debtor(debtor_id)
    if not debtor:
        await query.edit_message_text("❌ Topilmadi")
        return MAIN_MENU

    transactions = db.get_debtor_transactions(debtor_id)
    total_debt = sum(t['amount'] for t in transactions if t['type'] == 'debt')
    total_paid = sum(t['amount'] for t in transactions if t['type'] == 'payment')
    balance = total_debt - total_paid

    name = translate_text(debtor['name'], lang)
    phone = debtor.get('phone', '')

    if lang == "cyrillic":
        text = f"👤 <b>{name}</b>\n"
        if phone:
            text += f"📞 {phone}\n"
        text += f"\n💳 Умумий қарз: {format_money(total_debt)}"
        text += f"\n✅ Тўланган: {format_money(total_paid)}"
        text += f"\n🔴 Қолдиқ: <b>{format_money(balance)}</b>\n"
        text += "\n📜 <b>Тарих:</b>\n"
    else:
        text = f"👤 <b>{name}</b>\n"
        if phone:
            text += f"📞 {phone}\n"
        text += f"\n💳 Umumiy qarz: {format_money(total_debt)}"
        text += f"\n✅ To'langan: {format_money(total_paid)}"
        text += f"\n🔴 Qoldiq: <b>{format_money(balance)}</b>\n"
        text += "\n📜 <b>Tarix:</b>\n"

    for t in transactions[-10:]:  # Oxirgi 10 ta
        date = t['date'][:10]
        if t['type'] == 'debt':
            product = translate_text(t.get('description', ''), lang)
            text += f"  📌 {date}: +{format_money(t['amount'])} — {product}\n"
        else:
            text += f"  💵 {date}: -{format_money(t['amount'])} (to'lov)\n"

    if lang == "cyrillic":
        buttons = [
            [InlineKeyboardButton("💵 Тўлов қабул қилиш", callback_data=f"pay_{debtor_id}")],
            [InlineKeyboardButton("➕ Яна қарз қўшиш", callback_data=f"add_more_{debtor_id}")],
            [InlineKeyboardButton("🗑 Ўчириш", callback_data=f"delete_debtor_{debtor_id}"),
             InlineKeyboardButton("⬅️ Орқага", callback_data="all_debtors")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton("💵 To'lov qabul qilish", callback_data=f"pay_{debtor_id}")],
            [InlineKeyboardButton("➕ Yana qarz qo'shish", callback_data=f"add_more_{debtor_id}")],
            [InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_debtor_{debtor_id}"),
             InlineKeyboardButton("⬅️ Orqaga", callback_data="all_debtors")],
        ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return MAIN_MENU

async def show_report(query, lang):
    report = db.get_financial_report()

    if lang == "cyrillic":
        text = f"""📊 <b>Молиявий Ҳисобот</b>

💰 Жами кирим: {format_money(report['total_income'])}
💸 Жами чиқим: {format_money(report['total_expense'])}
📈 Фойда: {format_money(report['total_income'] - report['total_expense'])}

🔴 Жами қарз: {format_money(report['total_debt'])}
✅ Жами тўланган: {format_money(report['total_paid'])}
⏳ Тўланмаган: {format_money(report['total_debt'] - report['total_paid'])}

👥 Жами қарздорлар: {report['total_debtors']} та
⚠️ Муддати ўтганлар: {report['overdue_count']} та"""
    else:
        text = f"""📊 <b>Moliyaviy Hisobot</b>

💰 Jami kirim: {format_money(report['total_income'])}
💸 Jami chiqim: {format_money(report['total_expense'])}
📈 Foyda: {format_money(report['total_income'] - report['total_expense'])}

🔴 Jami qarz: {format_money(report['total_debt'])}
✅ Jami to'langan: {format_money(report['total_paid'])}
⏳ To'lanmagan: {format_money(report['total_debt'] - report['total_paid'])}

👥 Jami qarzdorlar: {report['total_debtors']} ta
⚠️ Muddati o'tganlar: {report['overdue_count']} ta"""

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]), parse_mode="HTML")
    return MAIN_MENU

async def show_settings(query, lang):
    if lang == "cyrillic":
        text = "⚙️ <b>Созламалар</b>\n\nТил танланг:"
        buttons = [
            [InlineKeyboardButton("🇺🇿 O'zbek lotin", callback_data="lang_latin"),
             InlineKeyboardButton("🇺🇿 Ўзбек Кирилл ✅" if lang == "cyrillic" else "🇺🇿 Ўзбек Кирилл", callback_data="lang_cyrillic")],
            [InlineKeyboardButton("💾 Backup yaratish", callback_data="backup_now")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")],
        ]
    else:
        text = "⚙️ <b>Sozlamalar</b>\n\nTil tanlang:"
        buttons = [
            [InlineKeyboardButton("🇺🇿 O'zbek lotin ✅", callback_data="lang_latin"),
             InlineKeyboardButton("🇺🇿 Ўзбек Кирилл", callback_data="lang_cyrillic")],
            [InlineKeyboardButton("💾 Backup yaratish", callback_data="backup_now")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")],
        ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return MAIN_MENU

# =================== MESSAGE HANDLERS ===================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return ConversationHandler.END

    lang = get_user_lang(user_id)
    text = update.message.text.strip()
    action = context.user_data.get('action', '')

    if action == 'add_debtor_name':
        context.user_data['debtor_name'] = text
        context.user_data['action'] = 'add_debtor_phone'
        if lang == "cyrillic":
            msg = "📞 Телефон рақамини киритинг (ихтиёрий, ўтказиш учун - ни босинг):"
        else:
            msg = "📞 Telefon raqamini kiriting (ixtiyoriy, o'tkazish uchun - ni bosing):"
        skip_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip_phone")]])
        await update.message.reply_text(msg, reply_markup=skip_btn)
        return ADD_DEBTOR_PHONE

    elif action == 'add_debtor_phone':
        context.user_data['debtor_phone'] = text
        return await ask_debt_product(update, context, lang)

    elif action == 'add_product':
        context.user_data['debt_product'] = text
        context.user_data['action'] = 'add_amount'
        if lang == "cyrillic":
            msg = "💰 Қарз суммасини киритинг (сўм):"
        else:
            msg = "💰 Qarz summasini kiriting (so'm):"
        await update.message.reply_text(msg)
        return ADD_DEBT_AMOUNT

    elif action == 'add_amount':
        try:
            amount = float(text.replace(" ", "").replace(",", ""))
            context.user_data['debt_amount'] = amount
            context.user_data['action'] = 'add_days'
            if lang == "cyrillic":
                msg = "📅 Неча кунда тўлайди? (рақам киритинг):"
            else:
                msg = "📅 Necha kunda to'laydi? (raqam kiriting):"
            skip_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Muddat yo'q", callback_data="skip_days")]])
            await update.message.reply_text(msg, reply_markup=skip_btn)
            return ADD_DEBT_DAYS
        except:
            if lang == "cyrillic":
                await update.message.reply_text("❌ Нотўғри сумма! Фақат рақам киритинг:")
            else:
                await update.message.reply_text("❌ Noto'g'ri summa! Faqat raqam kiriting:")
            return ADD_DEBT_AMOUNT

    elif action == 'add_days':
        try:
            days = int(text)
            context.user_data['debt_days'] = days
            return await save_debt(update, context, lang)
        except:
            if lang == "cyrillic":
                await update.message.reply_text("❌ Нотўғри сон! Рақам киритинг:")
            else:
                await update.message.reply_text("❌ Noto'g'ri son! Raqam kiriting:")
            return ADD_DEBT_DAYS

    elif action == 'search':
        results = db.search_debtor(text)
        if not results:
            if lang == "cyrillic":
                await update.message.reply_text("❌ Топилмади.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
            else:
                await update.message.reply_text("❌ Topilmadi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        else:
            buttons = []
            for d in results:
                name = translate_text(d['name'], lang)
                balance = d['total_debt'] - d['total_paid']
                label = f"👤 {name} — {format_money(balance)}"
                buttons.append([InlineKeyboardButton(label, callback_data=f"debtor_{d['id']}")])
            buttons.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")])
            if lang == "cyrillic":
                await update.message.reply_text(f"🔍 <b>{len(results)} та топилди:</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
            else:
                await update.message.reply_text(f"🔍 <b>{len(results)} ta topildi:</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        context.user_data['action'] = ''
        return MAIN_MENU

    elif action == 'income':
        try:
            amount = float(text.replace(" ", "").replace(",", ""))
            context.user_data['income_amount'] = amount
            context.user_data['action'] = 'income_desc'
            if lang == "cyrillic":
                await update.message.reply_text("📝 Изоҳ киритинг (ихтиёрий):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip_desc")]]));
            else:
                await update.message.reply_text("📝 Izoh kiriting (ixtiyoriy):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip_desc")]]))
            return INCOME_DESC
        except:
            await update.message.reply_text("❌ Raqam kiriting:")
            return INCOME_AMOUNT

    elif action == 'income_desc':
        amount = context.user_data.get('income_amount', 0)
        db.add_transaction('income', amount, text)
        if lang == "cyrillic":
            await update.message.reply_text(f"✅ Кирим қўшилди: {format_money(amount)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        else:
            await update.message.reply_text(f"✅ Kirim qo'shildi: {format_money(amount)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        context.user_data['action'] = ''
        return MAIN_MENU

    elif action == 'expense':
        try:
            amount = float(text.replace(" ", "").replace(",", ""))
            context.user_data['expense_amount'] = amount
            context.user_data['action'] = 'expense_desc'
            if lang == "cyrillic":
                await update.message.reply_text("📝 Изоҳ киритинг (ихтиёрий):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip_desc")]]))
            else:
                await update.message.reply_text("📝 Izoh kiriting (ixtiyoriy):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip_desc")]]))
            return EXPENSE_DESC
        except:
            await update.message.reply_text("❌ Raqam kiriting:")
            return EXPENSE_AMOUNT

    elif action == 'expense_desc':
        amount = context.user_data.get('expense_amount', 0)
        db.add_transaction('expense', amount, text)
        if lang == "cyrillic":
            await update.message.reply_text(f"✅ Чиқим қўшилди: {format_money(amount)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        else:
            await update.message.reply_text(f"✅ Chiqim qo'shildi: {format_money(amount)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        context.user_data['action'] = ''
        return MAIN_MENU

    elif action == 'add_payment':
        try:
            amount = float(text.replace(" ", "").replace(",", ""))
            debtor_id = context.user_data.get('pay_debtor_id')
            debtor = db.get_debtor(debtor_id)
            db.add_payment(debtor_id, amount)

            # Qolgan qarz
            balance_info = db.get_debtor_balance(debtor_id)
            remaining = balance_info['total_debt'] - balance_info['total_paid']

            name = translate_text(debtor['name'], lang)
            if lang == "cyrillic":
                if remaining <= 0:
                    msg = f"✅ Тўлов қабул қилинди!\n👤 {name}\n💵 Тўланди: {format_money(amount)}\n🎉 Қарз тўлиқ тўланди!"
                else:
                    msg = f"✅ Тўлов қабул қилинди!\n👤 {name}\n💵 Тўланди: {format_money(amount)}\n🔴 Қолдиқ: {format_money(remaining)}"
            else:
                if remaining <= 0:
                    msg = f"✅ To'lov qabul qilindi!\n👤 {name}\n💵 To'landi: {format_money(amount)}\n🎉 Qarz to'liq to'landi!"
                else:
                    msg = f"✅ To'lov qabul qilindi!\n👤 {name}\n💵 To'landi: {format_money(amount)}\n🔴 Qoldiq: {format_money(remaining)}"

            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Qarzdorga qaytish", callback_data=f"debtor_{debtor_id}")],
                [InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]
            ]))
            context.user_data['action'] = ''
            return MAIN_MENU
        except:
            await update.message.reply_text("❌ Raqam kiriting:")
            return ADD_PAYMENT

    # Default
    if lang == "cyrillic":
        await update.message.reply_text("Менюдан танланг:", reply_markup=main_keyboard(lang))
    else:
        await update.message.reply_text("Menyudan tanlang:", reply_markup=main_keyboard(lang))
    return MAIN_MENU

async def ask_debt_product(update, context, lang):
    context.user_data['action'] = 'add_product'
    if lang == "cyrillic":
        msg = "📦 Маҳсулот номини киритинг (масалан: нон, шакар):"
    else:
        msg = "📦 Mahsulot nomini kiriting (masalan: non, shakar):"
    await update.message.reply_text(msg)
    return ADD_DEBT_PRODUCT

async def save_debt(update, context, lang):
    debtor_id = context.user_data.get('existing_debtor_id')
    days = context.user_data.get('debt_days', None)
    due_date = None
    if days:
        due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    if debtor_id:
        # Mavjud qarzdorga qo'shish
        db.add_debt(debtor_id, context.user_data['debt_amount'], context.user_data['debt_product'], due_date)
    else:
        # Yangi qarzdor
        debtor_id = db.add_debtor(
            context.user_data['debtor_name'],
            context.user_data.get('debtor_phone', '')
        )
        db.add_debt(debtor_id, context.user_data['debt_amount'], context.user_data['debt_product'], due_date)

    debtor = db.get_debtor(debtor_id)
    balance = db.get_debtor_balance(debtor_id)
    total = balance['total_debt']
    name = translate_text(debtor['name'], lang)

    if lang == "cyrillic":
        msg = f"✅ Қарз қўшилди!\n\n👤 {name}\n📦 {context.user_data['debt_product']}\n💰 {format_money(context.user_data['debt_amount'])}\n📊 Жами қарз: {format_money(total)}"
        if days:
            msg += f"\n📅 Муддат: {days} кун ({due_date[:10]})"
    else:
        msg = f"✅ Qarz qo'shildi!\n\n👤 {name}\n📦 {context.user_data['debt_product']}\n💰 {format_money(context.user_data['debt_amount'])}\n📊 Jami qarz: {format_money(total)}"
        if days:
            msg += f"\n📅 Muddat: {days} kun ({due_date[:10]})"

    # Clear user data
    for key in ['debtor_name', 'debtor_phone', 'debt_product', 'debt_amount', 'debt_days', 'existing_debtor_id', 'action']:
        context.user_data.pop(key, None)

    buttons = [
        [InlineKeyboardButton("👤 Qarzdorni ko'rish", callback_data=f"debtor_{debtor_id}")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
    return MAIN_MENU

async def handle_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_user_lang(user_id)

    if query.data == "skip_phone":
        context.user_data['debtor_phone'] = ''
        context.user_data['action'] = 'add_product'
        if lang == "cyrillic":
            msg = "📦 Маҳсулот номини киритинг:"
        else:
            msg = "📦 Mahsulot nomini kiriting:"
        await query.edit_message_text(msg)
        return ADD_DEBT_PRODUCT

    elif query.data == "skip_days":
        context.user_data['debt_days'] = None
        # Fake update for save_debt
        context.user_data['action'] = ''
        # Create a mock message update
        debtor_id = context.user_data.get('existing_debtor_id')
        days = None
        due_date = None

        if debtor_id:
            db.add_debt(debtor_id, context.user_data['debt_amount'], context.user_data['debt_product'], due_date)
        else:
            debtor_id = db.add_debtor(
                context.user_data['debtor_name'],
                context.user_data.get('debtor_phone', '')
            )
            db.add_debt(debtor_id, context.user_data['debt_amount'], context.user_data['debt_product'], due_date)

        debtor = db.get_debtor(debtor_id)
        balance = db.get_debtor_balance(debtor_id)
        total = balance['total_debt']
        name = translate_text(debtor['name'], lang)

        if lang == "cyrillic":
            msg = f"✅ Қарз қўшилди!\n\n👤 {name}\n📦 {context.user_data['debt_product']}\n💰 {format_money(context.user_data['debt_amount'])}\n📊 Жами қарз: {format_money(total)}"
        else:
            msg = f"✅ Qarz qo'shildi!\n\n👤 {name}\n📦 {context.user_data['debt_product']}\n💰 {format_money(context.user_data['debt_amount'])}\n📊 Jami qarz: {format_money(total)}"

        for key in ['debtor_name', 'debtor_phone', 'debt_product', 'debt_amount', 'debt_days', 'existing_debtor_id', 'action']:
            context.user_data.pop(key, None)

        buttons = [
            [InlineKeyboardButton("👤 Qarzdorni ko'rish", callback_data=f"debtor_{debtor_id}")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
        return MAIN_MENU

    elif query.data == "skip_desc":
        action = context.user_data.get('action', '')
        if 'income' in action:
            amount = context.user_data.get('income_amount', 0)
            db.add_transaction('income', amount, '')
            if lang == "cyrillic":
                msg = f"✅ Кирим қўшилди: {format_money(amount)}"
            else:
                msg = f"✅ Kirim qo'shildi: {format_money(amount)}"
        else:
            amount = context.user_data.get('expense_amount', 0)
            db.add_transaction('expense', amount, '')
            if lang == "cyrillic":
                msg = f"✅ Чиқим қўшилди: {format_money(amount)}"
            else:
                msg = f"✅ Chiqim qo'shildi: {format_money(amount)}"

        context.user_data['action'] = ''
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]))
        return MAIN_MENU

    return MAIN_MENU

# =================== REMINDER SYSTEM ===================

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Har kuni muddati o'tgan qarzlar uchun eslatma yuborish"""
    overdue = db.get_overdue_debtors()
    backup_channel = os.getenv("BACKUP_CHANNEL_ID")

    for d in overdue:
        phone = d.get('phone', '')
        balance = d['total_debt'] - d['total_paid']
        days_over = d['days_overdue']
        name = d['name']

        # Do'kon egasiga xabar
        admins = get_admins()
        for admin_id in admins:
            lang = db.get_user_lang(admin_id)
            admin_name = translate_text(name, lang)
            try:
                if lang == "cyrillic":
                    msg = f"⚠️ <b>Муддати ўтди!</b>\n👤 {admin_name}\n💰 {format_money(balance)}\n📅 {days_over} кун кечикди"
                    if phone:
                        msg += f"\n📞 {phone}"
                else:
                    msg = f"⚠️ <b>Muddati o'tdi!</b>\n👤 {admin_name}\n💰 {format_money(balance)}\n📅 {days_over} kun kechikdi"
                    if phone:
                        msg += f"\n📞 {phone}"
                await context.bot.send_message(admin_id, msg, parse_mode="HTML")
            except:
                pass

async def daily_backup(context: ContextTypes.DEFAULT_TYPE):
    """Har kuni avtomatik backup"""
    await create_backup(context.bot)

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

    # ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ],
            ADD_DEBTOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(main_menu_callback),
            ],
            ADD_DEBTOR_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(handle_skip_callback),
            ],
            ADD_DEBT_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(main_menu_callback),
            ],
            ADD_DEBT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ],
            ADD_DEBT_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(handle_skip_callback),
            ],
            ADD_PAYMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(main_menu_callback),
            ],
            SEARCH_DEBTOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(main_menu_callback),
            ],
            INCOME_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ],
            INCOME_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(handle_skip_callback),
            ],
            EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ],
            EXPENSE_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(handle_skip_callback),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(main_menu_callback),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    # Job Queue - har kuni eslatma va backup
    job_queue = app.job_queue
    # Har kuni soat 09:00 da eslatma
    job_queue.run_daily(send_reminders, time=datetime.strptime("09:00", "%H:%M").time())
    # Har kuni soat 23:00 da backup
    job_queue.run_daily(daily_backup, time=datetime.strptime("23:00", "%H:%M").time())

    logger.info("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
