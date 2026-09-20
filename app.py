import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("8899030467:AAH4PQ2F3ceTlAWaZ-Y70t1Frz0h1b18POs")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💰 Earn", callback_data="earn"),
            InlineKeyboardButton("🎁 Bonus", callback_data="bonus"),
        ],
        [
            InlineKeyboardButton("📊 Balance", callback_data="balance"),
            InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton("👥 Invite Friends", callback_data="invite"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 Earn money\n"
        "🎁 Get bonus\n"
        "📊 Check balance\n"
        "💳 Withdraw\n"
        "👥 Invite your friends",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "earn":
        text = "💰 Earn\n\nEarn section is coming soon."

    elif query.data == "bonus":
        text = "🎁 Bonus\n\nYour bonus section is coming soon."

    elif query.data == "balance":
        text = "📊 Balance\n\nYour balance: ৳0"

    elif query.data == "withdraw":
        text = "💳 Withdraw\n\nWithdrawal system is coming soon."

    elif query.data == "invite":
        bot_username = context.bot.username
        invite_link = f"https://t.me/{bot_username}?start={query.from_user.id}"

        text = (
            "👥 Invite Friends\n\n"
            "Share your referral link with friends:\n\n"
            f"{invite_link}"
        )

    await query.edit_message_text(text)


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is not set in Environment Variables")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
