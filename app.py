from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8899030467:AAE7nWiRqZUY-oNF7XC6680sc9u1xqweXCA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 /earn\n🎁 /bonus\n📊 /balance\n💳 /withdraw"
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
