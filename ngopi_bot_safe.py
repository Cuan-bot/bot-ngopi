import os
from telegram import Update
from telegram.ext import Application, CommandHandler

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context):
    await update.message.reply_text("Bot $NGOPI is running! ✅")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
