import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("8899030467:AAFtPbpZBnpS9IwaGBuaZ6-7C3b1aPNPwNA")

# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def create_user(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def get_balance(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0


# =========================
# MAIN MENU
# =========================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Earn", callback_data="earn"),
            InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
        ],
        [
            InlineKeyboardButton("📊 Balance", callback_data="balance"),
            InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    create_user(user_id)

    await update.message.reply_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 Earn\n"
        "🎁 Bonus\n"
        "📊 Balance\n"
        "💳 Withdraw\n"
        "⚙️ Settings\n"
        "❓ Help\n\n"
        "👇 Select an option:",
        reply_markup=main_menu()
    )


# =========================
# EARN
# =========================

async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("📝 Available Task", callback_data="task")],
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ]

    await update.message.reply_text(
        "💰 Earn Section\n\n"
        "Complete available tasks to earn rewards.\n\n"
        "⚠️ Tasks and rewards will be added after the earning system is configured.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BONUS
# =========================

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus")],
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ]

    await update.message.reply_text(
        "🎁 Bonus Section\n\n"
        "Daily bonus system will be available here.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BALANCE
# =========================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    create_user(user_id)

    amount = get_balance(user_id)

    keyboard = [
        [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ]

    await update.message.reply_text(
        f"📊 Your Balance\n\n"
        f"💰 Balance: ৳{amount:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# WITHDRAW
# =========================

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ]

    await update.message.reply_text(
        "💳 Withdraw\n\n"
        "Minimum withdrawal amount and payment methods "
        "will be configured later.\n\n"
        "⚠️ Withdraw is not active yet.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    create_user(user_id)

    # HOME
    if query.data == "home":

        await query.edit_message_text(
            "🏠 Main Menu\n\n"
            "👇 Select an option:",
            reply_markup=main_menu()
        )

    # EARN
    elif query.data == "earn":

        keyboard = [
            [InlineKeyboardButton("📝 Available Task", callback_data="task")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]

        await query.edit_message_text(
            "💰 Earn Section\n\n"
            "Complete available tasks to earn rewards.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # TASK
    elif query.data == "task":

        keyboard = [
            [InlineKeyboardButton("⬅️ Earn", callback_data="earn")]
        ]

        await query.edit_message_text(
            "📝 Available Task\n\n"
            "No tasks are available right now.\n\n"
            "Admin can add tasks later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # BONUS
    elif query.data == "bonus":

        keyboard = [
            [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]

        await query.edit_message_text(
            "🎁 Bonus Section\n\n"
            "Daily bonus system will be available here.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # DAILY BONUS
    elif query.data == "daily_bonus":

        keyboard = [
            [InlineKeyboardButton("⬅️ Bonus", callback_data="bonus")]
        ]

        await query.edit_message_text(
            "🎁 Daily Bonus\n\n"
            "Bonus system is not active yet.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # BALANCE
    elif query.data == "balance":

        amount = get_balance(user_id)

        keyboard = [
            [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]

        await query.edit_message_text(
            f"📊 Your Balance\n\n"
            f"💰 Balance: ৳{amount:.2f}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # WITHDRAW
    elif query.data == "withdraw":

        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]

        await query.edit_message_text(
            "💳 Withdraw\n\n"
            "Withdraw system is not active yet.\n\n"
            "Minimum withdrawal and payment method "
            "will be configured later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # SETTINGS
    # =========================

    elif query.data == "settings":

        keyboard = [
            [InlineKeyboardButton("👤 Profile", callback_data="profile")],
            [InlineKeyboardButton("🔔 Notifications", callback_data="notifications")],
            [InlineKeyboardButton("🌐 Language", callback_data="language")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]

        await query.edit_message_text(
            "⚙️ Settings\n\n"
            "Choose a setting:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # PROFILE
    elif query.data == "profile":

        user = query.from_user

        username = (
            f"@{user.username}"
            if user.username
            else "Not set"
        )

        keyboard = [
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            f"👤 Profile\n\n"
            f"Name: {user.first_name}\n"
            f"Username: {username}\n"
            f"User ID: {user.id}\n"
            f"Balance: ৳{get_balance(user_id):.2f}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # NOTIFICATIONS
    elif query.data == "notifications":

        keyboard = [
            [InlineKeyboardButton("🔔 ON", callback_data="notification_on")],
            [InlineKeyboardButton("🔕 OFF", callback_data="notification_off")],
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            "🔔 Notifications\n\n"
            "Choose notification setting:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "notification_on":

        keyboard = [
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            "🔔 Notifications: ON",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "notification_off":

        keyboard = [
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            "🔕 Notifications: OFF",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # LANGUAGE
    elif query.data == "language":

        keyboard = [
            [InlineKeyboardButton("🇧🇩 বাংলা", callback_data="bangla")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="english")],
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            "🌐 Language\n\n"
            "Select your language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "bangla":

        keyboard = [
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            "🇧🇩 Language: বাংলা",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "english":

        keyboard = [
            [InlineKeyboardButton("⬅️ Settings", callback_data="settings")]
        ]

        await query.edit_message_text(
            "🇬🇧 Language: English",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # HELP
    # =========================

    elif query.data == "help":

        keyboard = [
            [InlineKeyboardButton("🤖 How to Use", callback_data="how_to_use")],
            [InlineKeyboardButton("💰 How to Earn", callback_data="how_to_earn")],
            [InlineKeyboardButton("💳 Withdraw Help", callback_data="withdraw_help")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="support")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]

        await query.edit_message_text(
            "❓ Help Center\n\n"
            "Choose what you need help with:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # HOW TO USE
    elif query.data == "how_to_use":

        keyboard = [
            [InlineKeyboardButton("⬅️ Help", callback_data="help")]
        ]

        await query.edit_message_text(
            "🤖 How to Use\n\n"
            "1️⃣ Start the bot\n"
            "2️⃣ Open Earn\n"
            "3️⃣ Complete available tasks\n"
            "4️⃣ Check your Balance\n"
            "5️⃣ Withdraw when eligible",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # HOW TO EARN
    elif query.data == "how_to_earn":

        keyboard = [
            [InlineKeyboardButton("⬅️ Help", callback_data="help")]
        ]

        await query.edit_message_text(
            "💰 How to Earn\n\n"
            "Complete legitimate tasks that are available in the bot.\n\n"
            "⚠️ Earnings are not guaranteed.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # WITHDRAW HELP
    elif query.data == "withdraw_help":

        keyboard = [
            [InlineKeyboardButton("⬅️ Help", callback_data="help")]
        ]

        await query.edit_message_text(
            "💳 Withdraw Help\n\n"
            "The withdrawal system is currently being configured.\n\n"
            "Minimum withdrawal and payment methods "
            "will be announced when active.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # SUPPORT
    elif query.data == "support":

        keyboard = [
            [InlineKeyboardButton("⬅️ Help", callback_data="help")]
        ]

        await query.edit_message_text(
            "📞 Contact Support\n\n"
            "Support system will be added later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN is missing. Add BOT_TOKEN in Render Environment Variables."
        )

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("withdraw", withdraw))

    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Income With Me Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
