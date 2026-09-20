import os
import sqlite3
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("8899030467:AAEJSTTmwl3dALeWYFh72_ayZxM5QMqrK_Q")

# Telegram numeric user ID(s) of administrators.
# Example:
# ADMIN_IDS = {123456789}
ADMIN_IDS = set()

DB_NAME = "income_with_me.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB_NAME)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            total_earned REAL DEFAULT 0,
            total_withdrawn REAL DEFAULT 0,
            referral_count INTEGER DEFAULT 0,
            referred_by INTEGER,
            joined_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            reward REAL NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_id INTEGER,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT,
            UNIQUE(user_id, task_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            description TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            account TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)

    con.commit()
    con.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# USER FUNCTIONS
# =========================================================

def get_user(user_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cur.fetchone()
    con.close()

    return user


def create_user(user, referred_by=None):
    con = db()
    cur = con.cursor()

    existing = get_user(user.id)

    if existing:
        con.close()
        return False

    cur.execute("""
        INSERT INTO users
        (id, username, first_name, referred_by, joined_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
        referred_by,
        now()
    ))

    if referred_by and referred_by != user.id:
        cur.execute("""
            UPDATE users
            SET referral_count = referral_count + 1
            WHERE id = ?
        """, (referred_by,))

    con.commit()
    con.close()

    return True


def add_balance(user_id, amount, description, transaction_type="earning"):
    con = db()
    cur = con.cursor()

    cur.execute("""
        UPDATE users
        SET balance = balance + ?,
            total_earned = total_earned + ?
        WHERE id = ?
    """, (amount, amount, user_id))

    cur.execute("""
        INSERT INTO transactions
        (user_id, amount, type, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        amount,
        transaction_type,
        description,
        now()
    ))

    con.commit()
    con.close()


# =========================================================
# KEYBOARD
# =========================================================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Earn", callback_data="earn"),
            InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
        ],
        [
            InlineKeyboardButton("👥 Invite", callback_data="invite"),
            InlineKeyboardButton("💳 Balance", callback_data="balance")
        ],
        [
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ]
    ])


# =========================================================
# /START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    referral_id = None

    if context.args:
        try:
            referral_id = int(context.args[0])
        except ValueError:
            referral_id = None

    is_new = create_user(user, referral_id)

    text = (
        "👋 Welcome to Income With Me!\n\n"
        "💰 Complete tasks and earn rewards.\n"
        "🎁 Claim bonuses.\n"
        "👥 Invite friends.\n"
        "💸 Request withdrawals.\n\n"
        "👇 Choose an option:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# EARN / TASKS
# =========================================================

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT id, title, description, reward
        FROM tasks
        WHERE active = 1
        ORDER BY id DESC
    """)

    tasks = cur.fetchall()
    con.close()

    if not tasks:
        await query.edit_message_text(
            "📋 No tasks are available right now.",
            reply_markup=main_keyboard()
        )
        return

    buttons = []

    for task_id, title, description, reward in tasks:
        buttons.append([
            InlineKeyboardButton(
                f"📋 {title} — ৳{reward:.2f}",
                callback_data=f"task_{task_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("⬅️ Back", callback_data="home")
    ])

    await query.edit_message_text(
        "💰 Available Tasks\n\nSelect a task:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def task_details(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    task_id = int(query.data.split("_")[1])

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT title, description, reward
        FROM tasks
        WHERE id = ? AND active = 1
    """, (task_id,))

    task = cur.fetchone()

    cur.execute("""
        SELECT status
        FROM submissions
        WHERE user_id = ? AND task_id = ?
    """, (query.from_user.id, task_id))

    submission = cur.fetchone()

    con.close()

    if not task:
        await query.edit_message_text(
            "❌ Task not found.",
            reply_markup=main_keyboard()
        )
        return

    title, description, reward = task

    if submission:
        status = submission[0]

        await query.edit_message_text(
            f"📋 {title}\n\n"
            f"{description}\n\n"
            f"💰 Reward: ৳{reward:.2f}\n"
            f"📌 Status: {status}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Tasks", callback_data="earn")]
            ])
        )
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Submit Task",
                callback_data=f"submit_{task_id}"
            )
        ],
        [
            InlineKeyboardButton("⬅️ Tasks", callback_data="earn")
        ]
    ])

    await query.edit_message_text(
        f"📋 {title}\n\n"
        f"{description}\n\n"
        f"💰 Reward: ৳{reward:.2f}",
        reply_markup=keyboard
    )


async def submit_task(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    task_id = int(query.data.split("_")[1])
    user_id = query.from_user.id

    con = db()
    cur = con.cursor()

    try:
        cur.execute("""
            INSERT INTO submissions
            (user_id, task_id, status, submitted_at)
            VALUES (?, ?, 'pending', ?)
        """, (user_id, task_id, now()))

        con.commit()

    except sqlite3.IntegrityError:
        con.close()

        await query.edit_message_text(
            "⚠️ You have already submitted this task.",
            reply_markup=main_keyboard()
        )
        return

    con.close()

    await query.edit_message_text(
        "✅ Task submitted!\n\n"
        "⏳ Your submission is waiting for admin verification.",
        reply_markup=main_keyboard()
    )


# =========================================================
# BONUS
# =========================================================

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    con = db()
    cur = con.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
        SELECT id
        FROM transactions
        WHERE user_id = ?
        AND type = 'daily_bonus'
        AND created_at LIKE ?
    """, (user_id, today + "%"))

    claimed = cur.fetchone()

    con.close()

    if claimed:
        text = "🎁 You have already claimed today's bonus."
    else:
        bonus_amount = 5

        add_balance(
            user_id,
            bonus_amount,
            "Daily bonus",
            "daily_bonus"
        )

        text = (
            "🎉 Daily Bonus Claimed!\n\n"
            f"💰 +৳{bonus_amount:.2f}"
        )

    await query.edit_message_text(
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# BALANCE
# =========================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if not user:
        await query.edit_message_text(
            "Please use /start first."
        )
        return

    balance_amount = user[3]
    total_earned = user[4]
    total_withdrawn = user[5]

    await query.edit_message_text(
        "💳 Your Balance\n\n"
        f"💰 Available: ৳{balance_amount:.2f}\n"
        f"📈 Total Earned: ৳{total_earned:.2f}\n"
        f"💸 Total Withdrawn: ৳{total_withdrawn:.2f}",
        reply_markup=main_keyboard()
    )


# =========================================================
# INVITE
# =========================================================

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    bot = await context.bot.get_me()

    referral_link = (
        f"https://t.me/{bot.username}?start={user_id}"
    )

    user = get_user(user_id)

    referrals = user[6] if user else 0

    await query.edit_message_text(
        "👥 Invite & Earn\n\n"
        f"Your referrals: {referrals}\n\n"
        "🔗 Your referral link:\n"
        f"{referral_link}\n\n"
        "Share this link with your friends.",
        reply_markup=main_keyboard()
    )


# =========================================================
# PROFILE
# =========================================================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if not user:
        await query.edit_message_text(
            "Please use /start first."
        )
        return

    await query.edit_message_text(
        "👤 Profile\n\n"
        f"🆔 User ID: {user[0]}\n"
        f"👤 Name: {user[2]}\n"
        f"📅 Joined: {user[8]}\n"
        f"👥 Referrals: {user[6]}\n"
        f"💰 Balance: ৳{user[3]:.2f}",
        reply_markup=main_keyboard()
    )


# =========================================================
# WITHDRAW
# =========================================================

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if not user:
        await query.edit_message_text(
            "Please use /start first."
        )
        return

    balance_amount = user[3]

    if balance_amount < 100:
        await query.edit_message_text(
            "💸 Withdraw\n\n"
            f"Your balance: ৳{balance_amount:.2f}\n\n"
            "Minimum withdrawal: ৳100\n\n"
            "Keep earning until you reach the minimum.",
            reply_markup=main_keyboard()
        )
        return

    await query.edit_message_text(
        "💸 Withdraw\n\n"
        f"Available balance: ৳{balance_amount:.2f}\n\n"
        "To keep this starter backend simple, "
        "withdrawal requests should be created through "
        "the admin workflow after collecting the user's "
        "payment method and account details securely.",
        reply_markup=main_keyboard()
    )


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id):
    return user_id in ADMIN_IDS


# =========================================================
# ADMIN COMMANDS
# =========================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only.")
        return

    await update.message.reply_text(
        "🔐 Admin Panel\n\n"
        "/stats - Statistics\n"
        "/users - User count\n"
        "/addtask title|description|reward\n"
        "/tasks - View tasks\n"
        "/approve TASK_SUBMISSION_ID\n"
        "/reject TASK_SUBMISSION_ID"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    con = db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE active = 1")
    tasks = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(balance), 0) FROM users"
    )
    balance_total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM withdrawals
        WHERE status = 'pending'
    """)
    pending_withdrawals = cur.fetchone()[0]

    con.close()

    await update.message.reply_text(
        "📊 Admin Statistics\n\n"
        f"👥 Users: {users}\n"
        f"📋 Active Tasks: {tasks}\n"
        f"💰 User Balances: ৳{balance_total:.2f}\n"
        f"💸 Pending Withdrawals: {pending_withdrawals}"
    )


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    con = db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]

    con.close()

    await update.message.reply_text(
        f"👥 Total users: {count}"
    )


async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    raw = update.message.text.replace("/addtask", "", 1).strip()

    parts = raw.split("|")

    if len(parts) != 3:
        await update.message.reply_text(
            "Format:\n"
            "/addtask Task title|Task description|10"
        )
        return

    title = parts[0].strip()
    description = parts[1].strip()

    try:
        reward = float(parts[2].strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Reward must be a number."
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO tasks
        (title, description, reward, active)
        VALUES (?, ?, ?, 1)
    """, (title, description, reward))

    con.commit()
    task_id = cur.lastrowid
    con.close()

    await update.message.reply_text(
        f"✅ Task created.\nTask ID: {task_id}"
    )


async def admin_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT id, title, reward, active
        FROM tasks
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    con.close()

    if not rows:
        await update.message.reply_text(
            "📋 No tasks found."
        )
        return

    text = "📋 Tasks\n\n"

    for task_id, title, reward, active in rows:
        status = "🟢 Active" if active else "🔴 Off"

        text += (
            f"#{task_id} — {title}\n"
            f"Reward: ৳{reward:.2f}\n"
            f"Status: {status}\n\n"
        )

    await update.message.reply_text(text)


# =========================================================
# APPROVE TASK SUBMISSION
# =========================================================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /approve SUBMISSION_ID"
        )
        return

    try:
        submission_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid submission ID."
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT user_id, task_id, status
        FROM submissions
        WHERE id = ?
    """, (submission_id,))

    submission = cur.fetchone()

    if not submission:
        con.close()

        await update.message.reply_text(
            "❌ Submission not found."
        )
        return

    user_id, task_id, status = submission

    if status != "pending":
        con.close()

        await update.message.reply_text(
            f"⚠️ Already processed: {status}"
        )
        return

    cur.execute("""
        SELECT reward, title
        FROM tasks
        WHERE id = ?
    """, (task_id,))

    task = cur.fetchone()

    if not task:
        con.close()

        await update.message.reply_text(
            "❌ Task no longer exists."
        )
        return

    reward, title = task

    cur.execute("""
        UPDATE submissions
        SET status = 'approved'
        WHERE id = ?
    """, (submission_id,))

    con.commit()
    con.close()

    add_balance(
        user_id,
        reward,
        f"Task approved: {title}",
        "task_reward"
    )

    await update.message.reply_text(
        f"✅ Submission approved.\n"
        f"💰 Reward added: ৳{reward:.2f}"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 Task Approved!\n\n"
                f"📋 {title}\n"
                f"💰 +৳{reward:.2f}"
            )
        )
    except Exception:
        pass


# =========================================================
# REJECT TASK SUBMISSION
# =========================================================

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /reject SUBMISSION_ID"
        )
        return

    try:
        submission_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid submission ID."
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
        UPDATE submissions
        SET status = 'rejected'
        WHERE id = ? AND status = 'pending'
    """, (submission_id,))

    changed = cur.rowcount

    con.commit()
    con.close()

    if changed:
        await update.message.reply_text(
            "❌ Submission rejected."
        )
    else:
        await update.message.reply_text(
            "⚠️ Submission not found or already processed."
        )


# =========================================================
# HOME BUTTON
# =========================================================

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 Earn rewards by completing available tasks.\n"
        "🎁 Claim your daily bonus.\n"
        "👥 Invite friends.\n"
        "💳 Check your balance.\n"
        "💸 Request withdrawals.\n\n"
        "👇 Choose an option:",
        reply_markup=main_keyboard()
    )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "home":
        await home(update, context)

    elif query.data == "earn":
        await show_tasks(update, context)

    elif query.data.startswith("task_"):
        await task_details(update, context)

    elif query.data.startswith("submit_"):
        await submit_task(update, context)

    elif query.data == "bonus":
        await bonus(update, context)

    elif query.data == "balance":
        await balance(update, context)

    elif query.data == "invite":
        await invite(update, context)

    elif query.data == "profile":
        await profile(update, context)

    elif query.data == "withdraw":
        await withdraw(update, context)


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # User commands
    application.add_handler(
        CommandHandler("start", start)
    )

    # Admin commands
    application.add_handler(
        CommandHandler("admin", admin)
    )

    application.add_handler(
        CommandHandler("stats", stats)
    )

    application.add_handler(
        CommandHandler("users", users)
    )

    application.add_handler(
        CommandHandler("addtask", addtask)
    )

    application.add_handler(
        CommandHandler("tasks", admin_tasks)
    )

    application.add_handler(
        CommandHandler("approve", approve)
    )

    application.add_handler(
        CommandHandler("reject", reject)
    )

    # Buttons
    application.add_handler(
        CallbackQueryHandler(callback_router)
    )

    print("🚀 Income With Me bot is running...")

    # IMPORTANT:
    # Only one bot process should use this token at a time.
    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
