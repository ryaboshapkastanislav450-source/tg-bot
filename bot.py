"""
Telegram Shop Bot — оплата через подарок звёздами
pip install python-telegram-bot==20.7
py -3.14 bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ═══════════════════════════════════════════════
#  ⚙️ НАСТРОЙКИ — заполни перед запуском
# ═══════════════════════════════════════════════
BOT_TOKEN      = "8994877694:AAGRndP8zbUGDgYToJ9QwvsSE_6pa_HnIa0"
ADMIN_ID       = 8153670251
ADMIN_USERNAME = "@platasignbot"

# ═══════════════════════════════════════════════
#  🛒 КАТАЛОГ СИГН
#  stars — количество звёзд (50 ⭐ ≈ $0.65)
# ═══════════════════════════════════════════════
CATALOG = {
    "item_1": {"name": "На ляшечках",  "stars": 50,  "desc": "Ляшечки"},
    "item_2": {"name": "В трсусиках на попе ",  "stars": 125, "desc": "Попочка"},
    "item_3": {"name": "На груди",      "stars": 150, "desc": "Сисички"},
    "item_4": {"name": "Без трусиков",        "stars": 250, "desc": "Без трусиков"},
}

# Состояния ConversationHandler
WAITING_USERNAME = 1

# Хранилище заказов { user_id: { item_key, item_name, stars, client_username } }
orders: dict = {}

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ───────────────────────────────────────────────
#  Клавиатура каталога
# ───────────────────────────────────────────────
def catalog_keyboard():
    keyboard = []
    for key, item in CATALOG.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{item['name']} — {item['stars']} ⭐",
                callback_data=f"buy_{key}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

# ───────────────────────────────────────────────
#  /start
# ───────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"🆔 Твой ID: <code>{user.id}</code>\n\n"
        "Выбери сигну из каталога 👇",
        reply_markup=catalog_keyboard(),
        parse_mode="HTML"
    )

# ───────────────────────────────────────────────
#  Нажал «купить» — плашка оплаты
# ───────────────────────────────────────────────
async def buy_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_key = query.data.replace("buy_", "")
    item     = CATALOG.get(item_key)
    if not item:
        await query.edit_message_text("❌ Товар не найден.")
        return ConversationHandler.END

    uid = query.from_user.id
    orders[uid] = {"item_key": item_key, "item_name": item["name"], "stars": item["stars"]}

    await query.edit_message_text(
        f"🛒 <b>{item['name']}</b>\n"
        f"📝 {item['desc']}\n\n"
        f"💫 Стоимость: <b>{item['stars']} ⭐ звёзд</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📲 <b>Как оплатить:</b>\n\n"
        f"1️⃣ Открой профиль <b>{ADMIN_USERNAME}</b>\n"
        f"2️⃣  «Отправь подароков на нужную суму» → выбери <b>{item['stars']} ⭐</b>\n"
        "3️⃣ Вернись сюда и нажми кнопку ниже ✅\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <i>После отправки подарка нажмите кнопку — без этого заказ не оформится</i>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Я оплатил!", callback_data=f"paid_{item_key}")],
            [InlineKeyboardButton("◀️ Назад к каталогу",   callback_data="catalog")],
        ]),
        parse_mode="HTML"
    )
    return WAITING_USERNAME

# ───────────────────────────────────────────────
#  Нажал «Я оплатил» — просим ник
# ───────────────────────────────────────────────
async def paid_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()

    item_key = query.data.replace("paid_", "")
    item     = CATALOG.get(item_key)
    uid      = query.from_user.id

    if uid not in orders:
        orders[uid] = {}
    orders[uid].update({
        "item_key":  item_key,
        "item_name": item["name"],
        "stars":     item["stars"],
    })

    await query.edit_message_text(
        "✍️ <b>Отлично!</b>\n\n"
        "Напишите ваш <b>Telegram-ник</b>\n"
        "Например: <code>@username</code>\n\n"
        "Это нужно чтобы я нашла ваш подарок и отправила сигну с вашим юзом.",
        parse_mode="HTML"
    )
    return WAITING_USERNAME

# ───────────────────────────────────────────────
#  Получили ник — уведомляем админа с кнопками
# ───────────────────────────────────────────────
async def receive_username(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    uid      = user.id
    username = update.message.text.strip()

    order = orders.get(uid)
    if not order or "item_name" not in order:
        await update.message.reply_text("❌ Заказ не найден. Начни сначала — /start")
        return ConversationHandler.END

    orders[uid]["client_username"] = username

    # Клиенту
    await update.message.reply_text(
        "⏳ <b>Заявка принята!</b>\n\n"
        f"🆔 Твой ID: <code>{uid}</code>\n"
        f"📦 Товар: <b>{order['item_name']}</b>\n"
        f"💫 Сумма: {order['stars']} ⭐\n"
        f"👤 Ник: {username}\n\n"
        "Администратор проверит оплату и скоро пришлёт заказ.\n"
        "⏱ Обычно до 30 минут.",
        parse_mode="HTML"
    )

    # Админу — с кнопками ✅ и ❌
    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"👤 Клиент: {user.first_name} ({username})\n"
            f"🆔 User ID: <code>{uid}</code>\n"
            f"📦 Товар: <b>{order['item_name']}</b>\n"
            f"💫 Звёзды: {order['stars']} ⭐\n\n"
            "Выбери действие:"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Отправить файл клиенту", callback_data=f"admin_send_{uid}")],
            [InlineKeyboardButton("❌ Оплата не получена",     callback_data=f"admin_reject_{uid}")],
        ]),
        parse_mode="HTML"
    )
    return ConversationHandler.END

# ───────────────────────────────────────────────
#  Кнопка «Отправить файл» — инструкция
# ───────────────────────────────────────────────
async def admin_send_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("Нет доступа.", show_alert=True)
        return
    await query.answer()

    target_uid = query.data.replace("admin_send_", "")

    await query.edit_message_text(
        query.message.text.split("\n\nВыбери")[0] + "\n\n"
        "📎 <b>Как отправить файл клиенту:</b>\n\n"
        "1️⃣ Отправь фото/файл/видео в этот чат\n"
        "2️⃣ Нажми на него → «Ответить»\n"
        f"3️⃣ Напиши команду: <code>/send {target_uid}</code>",
        parse_mode="HTML"
    )

# ───────────────────────────────────────────────
#  Кнопка «Оплата не получена» — пишет клиенту
# ───────────────────────────────────────────────
async def admin_reject_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("Нет доступа.", show_alert=True)
        return
    await query.answer()

    target_uid = int(query.data.replace("admin_reject_", ""))
    order      = orders.get(target_uid, {})
    item_name  = order.get("item_name", "товар")
    stars      = order.get("stars", "?")

    try:
        await ctx.bot.send_message(
            chat_id=target_uid,
            text=(
                "⚠️ <b>Оплата не найдена</b>\n\n"
                f"Мы не получили подарок за <b>{item_name}</b> ({stars} ⭐).\n\n"
                "Пожалуйста, убедитесь что:\n"
                f"✅ Подарок отправлен на аккаунт <b>{ADMIN_USERNAME}</b>\n"
                f"✅ Сумма подарка: <b>{stars} ⭐</b>\n\n"
                "После оплаты нажмите /start и оформите заказ снова.\n"
                "Если уверены что оплата прошла — напишите нам напрямую."
            ),
            parse_mode="HTML"
        )

        await query.edit_message_text(
            query.message.text.split("\n\nВыбери")[0] +
            "\n\n❌ <b>Клиент уведомлён об отсутствии оплаты</b>",
            parse_mode="HTML"
        )
        orders.pop(target_uid, None)

    except Exception as e:
        await query.edit_message_text(
            query.message.text + f"\n\n⚠️ Ошибка: {e}",
            parse_mode="HTML"
        )

# ───────────────────────────────────────────────
#  /send USER_ID — отправить файл клиенту
#  Ответь на фото/файл/видео и напиши /send 123456
# ───────────────────────────────────────────────
async def send_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    args = ctx.args
    if not args:
        await update.message.reply_text(
            "📌 <b>Использование:</b>\n\n"
            "Ответь на фото/файл/видео командой:\n"
            "<code>/send USER_ID</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_uid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID. Пример: <code>/send 123456789</code>", parse_mode="HTML")
        return

    order     = orders.get(target_uid, {})
    item_name = order.get("item_name", "заказ")
    caption   = f"✅ Твой заказ: <b>{item_name}</b>\n\nСпасибо за покупку! 💕"

    reply = update.message.reply_to_message
    sent  = False

    if reply:
        if reply.photo:
            # reply.photo — это список, берём последний элемент (наилучшее качество)
            best_photo = reply.photo[-1].file_id
            await ctx.bot.send_photo(
                chat_id=target_uid,
                photo=best_photo,
                caption=caption,
                parse_mode="HTML"
            )
            sent = True

        elif reply.document:
            await ctx.bot.send_document(
                chat_id=target_uid,
                document=reply.document.file_id,
                caption=caption,
                parse_mode="HTML"
            )
            sent = True

        elif reply.video:
            await ctx.bot.send_video(
                chat_id=target_uid,
                video=reply.video.file_id,
                caption=caption,
                parse_mode="HTML"
            )
            sent = True

        elif reply.audio:
            await ctx.bot.send_audio(
                chat_id=target_uid,
                audio=reply.audio.file_id,
                caption=caption,
                parse_mode="HTML"
            )
            sent = True

        elif reply.voice:
            await ctx.bot.send_voice(
                chat_id=target_uid,
                voice=reply.voice.file_id,
                caption=caption,
                parse_mode="HTML"
            )
            sent = True

        elif reply.text:
            await ctx.bot.send_message(
                chat_id=target_uid,
                text=f"✅ <b>{item_name}</b>\n\n{reply.text}\n\nСпасибо за покупку! 💕",
                parse_mode="HTML"
            )
            sent = True

    if sent:
        await update.message.reply_text(
            f"✅ Отправлено клиенту <code>{target_uid}</code>!",
            parse_mode="HTML"
        )
        orders.pop(target_uid, None)
    else:
        await update.message.reply_text(
            "⚠️ <b>Нужно ответить на файл!</b>\n\n"
            "Как это сделать:\n"
            "1️⃣ Отправь фото или файл в этот чат\n"
            "2️⃣ Нажми на него → «Ответить» (Reply)\n"
            f"3️⃣ Напиши: <code>/send {target_uid}</code>",
            parse_mode="HTML"
        )

# ───────────────────────────────────────────────
#  Назад к каталогу
# ───────────────────────────────────────────────
async def catalog_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Выбери товар из каталога 👇",
        reply_markup=catalog_keyboard()
    )
    return ConversationHandler.END

# ───────────────────────────────────────────────
#  /orders — активные заказы (только админ)
# ───────────────────────────────────────────────
async def show_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not orders:
        await update.message.reply_text("📭 Активных заказов нет.")
        return

    text = "📋 <b>Активные заказы:</b>\n\n"
    for uid, order in orders.items():
        text += (
            f"👤 {order.get('client_username', 'ник не указан')}\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📦 {order.get('item_name', '?')} — {order.get('stars', '?')} ⭐\n"
            f"📤 <code>/send {uid}</code>\n"
            "───────────\n"
        )
    await update.message.reply_text(text, parse_mode="HTML")

# ═══════════════════════════════════════════════
#  ЗАПУСК
# ═══════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_item,    pattern=r"^buy_"),
            CallbackQueryHandler(paid_button, pattern=r"^paid_"),
        ],
        states={
            WAITING_USERNAME: [
                CallbackQueryHandler(paid_button,  pattern=r"^paid_"),
                CallbackQueryHandler(catalog_back, pattern=r"^catalog$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(catalog_back, pattern=r"^catalog$"),
        ],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("send",   send_file))
    app.add_handler(CommandHandler("orders", show_orders))
    app.add_handler(CallbackQueryHandler(admin_send_callback, pattern=r"^admin_send_"))
    app.add_handler(CallbackQueryHandler(admin_reject_callback, pattern=r"^admin_reject_"))
    app.add_handler(conv)

    print("🤖 Бот запущен! Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
