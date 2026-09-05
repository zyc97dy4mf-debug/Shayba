import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# =========================
# SOZLAMALAR
# =========================

CARD_NUMBER = "1111 2222 3333 4444"

products = {
    1: {"name": "Tovar 1", "price": 10000},
    2: {"name": "Tovar 2", "price": 20000},
    3: {"name": "Tovar 3", "price": 30000},
    4: {"name": "Tovar 4", "price": 40000},
    5: {"name": "Tovar 5", "price": 50000},
    6: {"name": "Tovar 6", "price": 60000},
    7: {"name": "Tovar 7", "price": 70000},
}

carts = {}
blocked_users = set()


# =========================
# MENYU
# =========================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🛍 Tovarlar", "🛒 Savatim"],
            ["📦 Buyurtmam"],
        ],
        resize_keyboard=True
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "🛒 Market botiga xush kelibsiz.",
        reply_markup=main_menu()
    )


# =========================
# TOVARLAR
# =========================

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    text = "🛍 TOVARLAR\n\n"

    for number, product in products.items():
        text += (
            f"{number}. {product['name']}\n"
            f"💰 {product['price']:,} so'm\n\n"
        )

    text += "Tovar raqamini yuboring.\nMasalan: 1"

    await update.message.reply_text(text)


# =========================
# TOVAR TANLASH
# =========================

async def choose_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    text = update.message.text.strip()

    if not text.isdigit():
        return

    number = int(text)

    if number not in products:
        await update.message.reply_text("❌ Bunday tovar mavjud emas.")
        return

    carts.setdefault(user_id, [])
    carts[user_id].append(number)

    product = products[number]

    await update.message.reply_text(
        f"✅ Savatga qo‘shildi!\n\n"
        f"📦 {product['name']}\n"
        f"💰 {product['price']:,} so'm\n\n"
        f"Yana tovar tanlashingiz yoki 🛒 Savatimni bosishingiz mumkin.",
        reply_markup=main_menu()
    )


# =========================
# SAVAT
# =========================

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    cart = carts.get(user_id, [])

    if not cart:
        await update.message.reply_text("🛒 Savatingiz bo‘sh.")
        return

    text = "🛒 SAVATINGIZ\n\n"
    total = 0

    for number in cart:
        product = products[number]

        text += (
            f"• {product['name']} — "
            f"{product['price']:,} so'm\n"
        )

        total += product["price"]

    text += f"\n💰 JAMI: {total:,} so'm"

    location_button = KeyboardButton(
        "📍 Lokatsiyani yuborish",
        request_location=True
    )

    keyboard = ReplyKeyboardMarkup(
        [
            [location_button],
            ["🛍 Tovarlar", "🛒 Savatim"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        text + "\n\nYetkazib berish uchun lokatsiyangizni yuboring.",
        reply_markup=keyboard
    )


# =========================
# LOKATSIYA
# =========================

async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    cart = carts.get(user_id, [])

    if not cart:
        await update.message.reply_text(
            "❌ Avval savatga tovar qo‘shing."
        )
        return

    total = sum(products[x]["price"] for x in cart)

    await update.message.reply_text(
        f"📍 Lokatsiyangiz qabul qilindi.\n\n"
        f"💰 To‘lov summasi: {total:,} so'm\n\n"
        f"💳 Karta:\n"
        f"{CARD_NUMBER}\n\n"
        f"To‘lovni amalga oshiring va chekni "
        f"shu botga yuboring. 🧾"
    )

    if ADMIN_ID:
        await context.bot.send_location(
            chat_id=ADMIN_ID,
            latitude=update.message.location.latitude,
            longitude=update.message.location.longitude
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📦 YANGI BUYURTMA!\n\n"
                f"👤 {update.effective_user.full_name}\n"
                f"🆔 {user_id}\n"
                f"💰 {total:,} so'm"
            )
        )


# =========================
# CHEK
# =========================

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    if not ADMIN_ID:
        return

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🧾 CHEK YUBORILDI!\n\n"
            f"👤 {update.effective_user.full_name}\n"
            f"🆔 {user_id}\n\n"
            "⚠️ To‘lovni kartadan tekshiring."
        )
    )

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

    await update.message.reply_text(
        "🧾 Chekingiz qabul qilindi.\n\n"
        "⏳ To‘lov tekshirilmoqda."
    )


# =========================
# ADMIN
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "🔐 ADMIN PANEL\n\n"
        "Tovarni o‘zgartirish:\n"
        "/set 1 Tovar nomi 25000\n\n"
        "Masalan:\n"
        "/set 1 Coca Cola 15000\n\n"
        "Foydalanuvchini bloklash:\n"
        "/block 123456789\n\n"
        "Blokdan chiqarish:\n"
        "/unblock 123456789\n\n"
        "Tovarlarni ko‘rish:\n"
        "/products"
    )


# =========================
# ADMIN — TOVAR O‘ZGARTIRISH
# =========================

async def set_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Format noto‘g‘ri.\n\n"
            "/set 1 Tovar nomi 25000"
        )
        return

    try:
        number = int(context.args[0])
        price = int(context.args[-1])
        name = " ".join(context.args[1:-1])

        if number not in products:
            await update.message.reply_text(
                "❌ Tovar raqami 1 dan 7 gacha bo‘lishi kerak."
            )
            return

        products[number]["name"] = name
        products[number]["price"] = price

        await update.message.reply_text(
            f"✅ Tovar yangilandi!\n\n"
            f"📦 {name}\n"
            f"💰 {price:,} so'm"
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Narxni raqam bilan yozing."
        )


# =========================
# ADMIN — TOVARLARNI KO‘RISH
# =========================

async def admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "📦 TOVARLAR:\n\n"

    for number, product in products.items():
        text += (
            f"{number}. {product['name']} — "
            f"{product['price']:,} so'm\n"
        )

    await update.message.reply_text(text)


# =========================
# ADMIN — BLOKLASH
# =========================

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "/block USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
        blocked_users.add(user_id)

        await update.message.reply_text(
            f"🚫 {user_id} bloklandi."
        )

    except ValueError:
        await update.message.reply_text("❌ ID noto‘g‘ri.")


# =========================
# ADMIN — BLOKDAN CHIQARISH
# =========================

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "/unblock USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
        blocked_users.discard(user_id)

        await update.message.reply_text(
            f"✅ {user_id} blokdan chiqarildi."
        )

    except ValueError:
        await update.message.reply_text("❌ ID noto‘g‘ri.")


# =========================
# MATN
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in blocked_users:
        return

    text = update.message.text

    if text == "🛍 Tovarlar":
        await show_products(update, context)

    elif text == "🛒 Savatim":
        await show_cart(update, context)

    elif text == "📦 Buyurtmam":
        await update.message.reply_text(
            "📦 Buyurtmangiz to‘lov tekshirilgandan "
            "keyin tasdiqlanadi."
        )

    elif text == "📍 Lokatsiyani yuborish":
        await update.message.reply_text(
            "📍 Pastdagi tugma orqali lokatsiyani yuboring."
        )

    else:
        await choose_product(update, context)


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("set", set_product))
    app.add_handler(CommandHandler("products", admin_products))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))

    app.add_handler(
        MessageHandler(filters.LOCATION, receive_location)
    )

    app.add_handler(
        MessageHandler(filters.PHOTO, receive_receipt)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("BOT ISHLADI!")
    app.run_polling()


if __name__ == "__main__":
    main()
