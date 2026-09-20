from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8899030467:AAFtPbpZBnpS9IwaGBuaZ6-7C3b1aPNPwNA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 /earn\n"
        "🎁 /bonus\n"
        "📊 /balance\n"
        "💳 /withdraw"
    )

async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Earn section coming soon!")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 Bonus section coming soon!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Your balance: 0")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 Withdraw section coming soon!")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("earn", earn))
app.add_handler(CommandHandler("bonus", bonus))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("withdraw", withdraw))

app.run_polling()
