import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== KONFIGURASI ==========
TOKEN = "8344053127:AAEZCI_a1gOWiB5zJz6j185L1ESZuRPROP4"  # Ganti dengan token dari @BotFather
ADMIN_ID = 8236249613  # Ganti dengan ID Telegram kamu (ambil dari @userinfobot)
TOKEN_NAME = "NGOPI"
MINING_RATE = 0.001  # 0.001 token per detik

# ========== DATABASE ==========
# Format: {user_id: {"balance": 0, "last_claim": "timestamp", "total_mined": 0, "name": "username"}}
user_data = {}

def load_data():
    try:
        with open("ngopi_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data():
    with open("ngopi_data.json", "w") as f:
        json.dump(user_data, f)

user_data = load_data()

# ========== FUNGSI BANTUAN ==========
async def get_user(user_id: str, name: str) -> dict:
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0,
            "last_claim": datetime.now().isoformat(),
            "total_mined": 0,
            "name": name,
            "withdraw_request": None
        }
        save_data()
    return user_data[user_id]

async def calculate_pending(user_id: str) -> float:
    user = await get_user(user_id, "")
    last_claim = datetime.fromisoformat(user["last_claim"])
    seconds_passed = (datetime.now() - last_claim).total_seconds()
    seconds_passed = min(seconds_passed, 86400)  # Maks 24 jam
    return seconds_passed * MINING_RATE

def format_number(num: float) -> str:
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    return f"{num:.2f}"

# ========== COMMAND /START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    await get_user(user_id, user.first_name)
    
    keyboard = [
        [InlineKeyboardButton("⛏️ CLAIM", callback_data="claim")],
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="dashboard")],
        [InlineKeyboardButton("👥 REFERRAL", callback_data="referral")],
        [InlineKeyboardButton("💸 WITHDRAW", callback_data="withdraw")]
    ]
    
    await update.message.reply_text(
        f"☕ *{TOKEN_NAME} MINER* ☕\n\n"
        f"Halo {user.first_name}!\n\n"
        f"💎 Mining rate: `{MINING_RATE} {TOKEN_NAME}/detik`\n"
        f"📈 ~`{MINING_RATE*3600:.0f} {TOKEN_NAME}/jam`\n\n"
        f"Klik CLAIM setiap hari untuk mengumpulkan token!\n"
        f"Minimal withdraw: `1000 {TOKEN_NAME}`\n\n"
        f"🪙 *Total Supply:* 1.000.000.000 {TOKEN_NAME}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ========== CLAIM ==========
async def handle_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = await get_user(user_id, query.from_user.first_name)
    
    pending = await calculate_pending(user_id)
    
    if pending > 0:
        user["balance"] += pending
        user["total_mined"] += pending
        user["last_claim"] = datetime.now().isoformat()
        save_data()
        
        await query.edit_message_text(
            f"✅ *Claim Berhasil!*\n\n"
            f"⛏️ Dapat: `{pending:.2f} {TOKEN_NAME}`\n"
            f"💰 Total balance: `{user['balance']:.2f} {TOKEN_NAME}`\n\n"
            f"Kembali lagi nanti untuk lanjut mining! ☕",
            parse_mode="Markdown"
        )
    else:
        next_claim = datetime.fromisoformat(user["last_claim"]) + timedelta(seconds=10)
        wait_seconds = int((next_claim - datetime.now()).total_seconds())
        
        await query.edit_message_text(
            f"⏳ *Belum waktunya claim!*\n\n"
            f"Tunggu `{wait_seconds}` detik lagi.\n\n"
            f"💰 Balance saat ini: `{user['balance']:.2f} {TOKEN_NAME}`",
            parse_mode="Markdown"
        )

# ========== DASHBOARD ==========
async def handle_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = await get_user(user_id, query.from_user.first_name)
    pending = await calculate_pending(user_id)
    
    text = (
        f"📊 *{TOKEN_NAME} DASHBOARD*\n\n"
        f"👤 User: `{user['name']}`\n"
        f"💰 Balance: `{user['balance']:.2f} {TOKEN_NAME}`\n"
        f"⏳ Pending: `{pending:.2f} {TOKEN_NAME}`\n"
        f"📈 Total Mined: `{user['total_mined']:.2f} {TOKEN_NAME}`\n"
        f"⚡ Rate: `{MINING_RATE}` {TOKEN_NAME}/detik\n\n"
        f"💸 Minimal Withdraw: `1000 {TOKEN_NAME}`\n"
        f"🔗 Withdraw via admin (manual)"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== REFERRAL ==========
async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = await get_user(user_id, query.from_user.first_name)
    
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = (
        f"👥 *{TOKEN_NAME} REFERRAL*\n\n"
        f"🎁 Ajak teman dan dapatkan bonus!\n"
        f"💰 Bonus: `50 {TOKEN_NAME}` per referral\n"
        f"💸 Bonus 5% dari mining referral\n\n"
        f"🔗 *Link referral kamu:*\n"
        f"`{referral_link}`\n\n"
        f"👥 Total referral: `{len(user.get('referrals', []))}`"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== WITHDRAW ==========
async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = await get_user(user_id, query.from_user.first_name)
    
    if user["balance"] < 1000:
        await query.edit_message_text(
            f"❌ *Saldo tidak mencukupi!*\n\n"
            f"💰 Balance: `{user['balance']:.2f} {TOKEN_NAME}`\n"
            f"💸 Minimal withdraw: `1000 {TOKEN_NAME}`\n\n"
            f"Terus mining sampai mencapai minimal withdraw!",
            parse_mode="Markdown"
        )
        return
    
    # Kirim request ke admin
    admin_text = (
        f"🔔 *REQUEST WITHDRAW*\n\n"
        f"👤 User: {query.from_user.first_name} (@{query.from_user.username})\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Amount: `{user['balance']:.2f} {TOKEN_NAME}`\n\n"
        f"Balas dengan command:\n"
        f"`/approve {user_id} {TOKEN_NAME}`\n"
        f"`/reject {user_id}`"
    )
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    
    # Simpan request
    user["withdraw_request"] = {
        "amount": user["balance"],
        "timestamp": datetime.now().isoformat()
    }
    save_data()
    
    await query.edit_message_text(
        f"✅ *Request Withdraw Dikirim!*\n\n"
        f"💰 Amount: `{user['balance']:.2f} {TOKEN_NAME}`\n\n"
        f"Admin akan memproses dalam 1x24 jam.\n"
        f"Token akan dikirim ke wallet kamu setelah approved.\n\n"
        f"⚠️ Jangan lupa hubungkan wallet dengan command:\n"
        f"`/wallet <alamat_wallet_solana>`",
        parse_mode="Markdown"
    )

# ========== WALLET COMMAND ==========
async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = await get_user(user_id, update.effective_user.first_name)
    
    args = context.args
    if not args:
        current_wallet = user.get("wallet_address", "Belum diisi")
        await update.message.reply_text(
            f"🔗 *Wallet Info*\n\n"
            f"Wallet saat ini: `{current_wallet}`\n\n"
            f"Gunakan: `/wallet <alamat_wallet_solana>`\n"
            f"Contoh: `/wallet 7xKXk2xZ...`",
            parse_mode="Markdown"
        )
        return
    
    wallet_address = args[0]
    if len(wallet_address) not in [32, 44]:
        await update.message.reply_text("❌ Alamat wallet tidak valid!")
        return
    
    user["wallet_address"] = wallet_address
    save_data()
    
    await update.message.reply_text(
        f"✅ *Wallet berhasil dihubungkan!*\n\n"
        f"📤 Alamat: `{wallet_address[:10]}...{wallet_address[-6:]}`\n\n"
        f"Withdraw akan dikirim ke wallet ini.",
        parse_mode="Markdown"
    )

# ========== ADMIN COMMANDS ==========
async def approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Bukan admin!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Gunakan: `/approve <user_id> <token>`", parse_mode="Markdown")
        return
    
    user_id = args[0]
    token_symbol = args[1] if len(args) > 1 else TOKEN_NAME
    
    if user_id not in user_data:
        await update.message.reply_text("❌ User tidak ditemukan!")
        return
    
    user = user_data[user_id]
    if not user.get("wallet_address"):
        await update.message.reply_text(f"❌ User belum daftar wallet! Kirim: `/remind {user_id}`", parse_mode="Markdown")
        return
    
    amount = user["balance"]
    wallet = user["wallet_address"]
    
    # Reset balance setelah approve
    user["balance"] = 0
    user["withdraw_request"] = None
    save_data()
    
    await update.message.reply_text(
        f"✅ *Withdraw Approved!*\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Amount: `{amount:.2f} {token_symbol}`\n"
        f"📤 Wallet: `{wallet[:10]}...{wallet[-6:]}`\n\n"
        f"⚠️ JANGAN LUPA transfer token secara manual!",
        parse_mode="Markdown"
    )
    
    # Notifikasi ke user
    await context.bot.send_message(
        chat_id=int(user_id),
        text=f"🎉 *Withdraw Approved!*\n\n"
             f"💰 `{amount:.2f} {token_symbol}` akan dikirim ke wallet kamu.\n"
             f"📤 Wallet: `{wallet[:10]}...{wallet[-6:]}`\n\n"
             f"Terima kasih sudah mining {TOKEN_NAME}! ☕",
        parse_mode="Markdown"
    )

async def reject_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Bukan admin!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Gunakan: `/reject <user_id>`", parse_mode="Markdown")
        return
    
    user_id = args[0]
    
    if user_id not in user_data:
        await update.message.reply_text("❌ User tidak ditemukan!")
        return
    
    user = user_data[user_id]
    user["withdraw_request"] = None
    save_data()
    
    await update.message.reply_text(f"✅ Withdraw request untuk user `{user_id}` ditolak.", parse_mode="Markdown")
    
    await context.bot.send_message(
        chat_id=int(user_id),
        text=f"❌ *Withdraw Ditolak!*\n\n"
             f"Request withdraw kamu ditolak admin.\n"
             f"Pastikan wallet sudah dihubungkan dan saldo mencukupi.",
        parse_mode="Markdown"
    )

async def remind_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Bukan admin!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Gunakan: `/remind <user_id>`", parse_mode="Markdown")
        return
    
    user_id = args[0]
    
    await context.bot.send_message(
        chat_id=int(user_id),
        text=f"⚠️ *Pengingat: Hubungkan Wallet!*\n\n"
             f"Kamu memiliki saldo `{user_data[user_id]['balance']:.2f} {TOKEN_NAME}`.\n"
             f"Gunakan command `/wallet <alamat_wallet_solana>` untuk bisa withdraw.",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"✅ Reminder terkirim ke user `{user_id}`.", parse_mode="Markdown")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_data:
        await update.message.reply_text("Belum ada data.")
        return
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1].get("total_mined", 0), reverse=True)[:10]
    
    text = "🏆 *LEADERBOARD MINING* 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} `{data.get('name', 'Unknown')}`: `{data.get('total_mined', 0):.0f}` {TOKEN_NAME}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== BACK BUTTON ==========
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⛏️ CLAIM", callback_data="claim")],
        [InlineKeyboardButton("📊 DASHBOARD", callback_data="dashboard")],
        [InlineKeyboardButton("👥 REFERRAL", callback_data="referral")],
        [InlineKeyboardButton("💸 WITHDRAW", callback_data="withdraw")]
    ]
    
    await query.edit_message_text(
        f"☕ *{TOKEN_NAME} MINER* ☕\n\n"
        f"Klik CLAIM setiap hari untuk mining!\n\n"
        f"💎 Rate: `{MINING_RATE}` {TOKEN_NAME}/detik\n"
        f"💸 Minimal withdraw: `1000 {TOKEN_NAME}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== MAIN ==========
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Command
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wallet", wallet_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # Admin Commands
    app.add_handler(CommandHandler("approve", approve_withdraw))
    app.add_handler(CommandHandler("reject", reject_withdraw))
    app.add_handler(CommandHandler("remind", remind_wallet))
    
    # Callback
    app.add_handler(CallbackQueryHandler(handle_claim, pattern="^claim$"))
    app.add_handler(CallbackQueryHandler(handle_dashboard, pattern="^dashboard$"))
    app.add_handler(CallbackQueryHandler(handle_referral, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(handle_withdraw, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))
    
    print(f"🤖 {TOKEN_NAME} Miner Bot berjalan...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
