import os
import sqlite3
from datetime import datetime, date

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("8899030467:AAH4PQ2F3ceTlAWaZ-Y70t1Frz0h1b18POs")

# তোমার Telegram numeric user ID এখানে দাও
ADMIN_ID = int(os.getenv("01516572969", "0"))

MIN_WITHDRAW = 100
COINS_PER_TAKA = 1

DB_NAME = "bot.db"


# =========================
# DATABASE
# =========================

def db():
    return sqlite3.connect(DB_NAME)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            referred_by INTEGER,
            joined_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            reward INTEGER NOT NULL,
            link TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id INTEGER,
            task_id INTEGER,
            completed_at TEXT,
            PRIMARY KEY(user_id, task_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            method TEXT,
            account TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    """)

    con.commit()
    con.close()


def add_user(user_id, username, referred_by=None):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO users
            (user_id, username, balance, referred_by, joined_at)
            VALUES (?, ?, 0, ?, ?)
        """, (
            user_id,
            username or "",
            referred_by,
            datetime.now().isoformat()
        ))

    con.commit()
    con.close()


def get_balance(user_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()
    con.close()

    return row[0] if row else 0


def change_balance(user_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE user_id=?
    """, (amount, user_id))

    con.commit()
    con.close()


# =========================
# MAIN MENU
# =========================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Earn Tasks", callback_data="tasks"),
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="bonus"),
        ],
        [
            InlineKeyboardButton("👥 Invite Friends", callback_data="invite"),
            InlineKeyboardButton("📊 Balance", callback_data="balance"),
        ],
        [
            InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    referred_by = None

    # /start 123456
    if context.args:
        try:
            ref_id = int(context.args[0])

            if ref_id != user.id:
                referred_by = ref_id

        except ValueError:
            pass

    add_user(
        user.id,
        user.username,
        referred_by
    )

    # Referral reward
    if referred_by:
        con = db()
        cur = con.cursor()

        cur.execute("""
            SELECT referred_by
            FROM users
            WHERE user_id=?
        """, (user.id,))

        row = cur.fetchone()

        # New user's inviter gets reward only once
        cur.execute("""
            SELECT balance
            FROM users
            WHERE user_id=?
        """, (referred_by,))

        inviter = cur.fetchone()

        if inviter:
            cur.execute("""
                UPDATE users
                SET balance = balance + 20
                WHERE user_id=?
            """, (referred_by,))

        con.commit()
        con.close()

    await update.message.reply_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 Earn coins by completing tasks.\n"
        "👥 Invite friends and earn referral rewards.\n"
        "🎁 Claim your daily bonus.\n"
        "💳 Withdraw when you reach the minimum balance.\n\n"
        "Choose an option below:",
        reply_markup=main_menu()
    )


# =========================
# TASKS
# =========================

async def show_tasks(query):

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT task_id, title, reward, link
        FROM tasks
        WHERE active=1
    """)

    tasks = cur.fetchall()
    con.close()

    if not tasks:
        await query.edit_message_text(
            "📭 No tasks are available right now.",
            reply_markup=main_menu()
        )
        return

    buttons = []

    for task_id, title, reward, link in tasks:

        buttons.append([
            InlineKeyboardButton(
                f"📋 {title} (+{reward})",
                url=link
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                "✅ Complete",
                callback_data=f"complete:{task_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("⬅️ Back", callback_data="home")
    ])

    await query.edit_message_text(
        "💰 Available Tasks\n\n"
        "Complete a task and then press the Complete button.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def complete_task(query, task_id):

    user_id = query.from_user.id

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT reward, title
        FROM tasks
        WHERE task_id=? AND active=1
    """, (task_id,))

    task = cur.fetchone()

    if not task:
        con.close()

        await query.answer(
            "Task not found.",
            show_alert=True
        )
        return

    reward, title = task

    cur.execute("""
        SELECT user_id
        FROM completed_tasks
        WHERE user_id=? AND task_id=?
    """, (user_id, task_id))

    completed = cur.fetchone()

    if completed:
        con.close()

        await query.answer(
            "You already completed this task.",
            show_alert=True
        )
        return

    cur.execute("""
        INSERT INTO completed_tasks
        (user_id, task_id, completed_at)
        VALUES (?, ?, ?)
    """, (
        user_id,
        task_id,
        datetime.now().isoformat()
    ))

    cur.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE user_id=?
    """, (reward, user_id))

    con.commit()
    con.close()

    await query.answer(
        f"✅ +{reward} coins added!",
        show_alert=True
    )


# =========================
# DAILY BONUS
# =========================

bonus_users = {}


async def daily_bonus(query):

    user_id = query.from_user.id
    today = date.today().isoformat()

    if bonus_users.get(user_id) == today:

        await query.answer(
            "🎁 You already claimed today's bonus.",
            show_alert=True
        )
        return

    bonus_users[user_id] = today

    reward = 10

    change_balance(user_id, reward)

    await query.answer(
        f"🎁 Daily bonus +{reward} coins!",
        show_alert=True
    )


# =========================
# INVITE
# =========================

async def invite(query, bot_username):

    user_id = query.from_user.id

    link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        "👥 Invite Friends\n\n"
        "Share your referral link with friends.\n\n"
        f"🎁 Referral reward: 20 coins\n\n"
        "🔗 Your referral link:\n"
        f"{link}"
    )

    buttons = [
        [
            InlineKeyboardButton(
                "📤 Share Link",
                url=(
                    "https://t.me/share/url"
                    f"?url={link}"
                    "&text=Join%20Income%20With%20Me!"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================
# BALANCE
# =========================

async def balance(query):

    user_id = query.from_user.id
    amount = get_balance(user_id)

    await query.edit_message_text(
        f"📊 Your Balance\n\n"
        f"💰 Coins: {amount}\n"
        f"💵 Withdrawable: {amount} coins\n\n"
        f"Minimum withdrawal: {MIN_WITHDRAW} coins",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 Withdraw",
                    callback_data="withdraw"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================
# WITHDRAW
# =========================

withdraw_state = {}


async def withdraw_start(query):

    user_id = query.from_user.id
    amount = get_balance(user_id)

    if amount < MIN_WITHDRAW:

        await query.answer(
            f"Minimum withdrawal is {MIN_WITHDRAW} coins.",
            show_alert=True
        )
        return

    withdraw_state[user_id] = {
        "step": "amount"
    }

    await query.edit_message_text(
        f"💳 Withdraw\n\n"
        f"Your balance: {amount} coins\n"
        f"Minimum: {MIN_WITHDRAW} coins\n\n"
        "Send the amount you want to withdraw."
    )


# =========================
# MESSAGE HANDLER
# =========================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    if user_id not in withdraw_state:
        return

    state = withdraw_state[user_id]

    # Amount
    if state["step"] == "amount":

        try:
            amount = int(update.message.text)
        except ValueError:

            await update.message.reply_text(
                "❌ Please enter a valid number."
            )
            return

        balance_amount = get_balance(user_id)

        if amount < MIN_WITHDRAW:

            await update.message.reply_text(
                f"❌ Minimum withdrawal is {MIN_WITHDRAW} coins."
            )
            return

        if amount > balance_amount:

            await update.message.reply_text(
                "❌ Insufficient balance."
            )
            return

        state["amount"] = amount
        state["step"] = "method"

        await update.message.reply_text(
            "💳 Select payment method:\n\n"
            "Type one:\n"
            "bKash\n"
            "Nagad\n"
            "Rocket"
        )

        return

    # Payment method
    if state["step"] == "method":

        method = update.message.text.strip()

        if method.lower() not in ["bkash", "nagad", "rocket"]:

            await update.message.reply_text(
                "❌ Please type bKash, Nagad or Rocket."
            )
            return

        state["method"] = method
        state["step"] = "account"

        await update.message.reply_text(
            f"📱 Send your {method} account number."
        )

        return

    # Account
    if state["step"] == "account":

        account = update.message.text.strip()

        amount = state["amount"]
        method = state["method"]

        con = db()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO withdrawals
            (user_id, amount, method, account, status, created_at)
            VALUES (?, ?, ?, ?, 'Pending', ?)
        """, (
            user_id,
            amount,
            method,
            account,
            datetime.now().isoformat()
        ))

        withdrawal_id = cur.lastrowid

        # Reserve/remove balance
        cur.execute("""
            UPDATE users
            SET balance = balance - ?
            WHERE user_id=?
        """, (amount, user_id))

        con.commit()
        con.close()

        del withdraw_state[user_id]

        await update.message.reply_text(
            "✅ Withdrawal request submitted!\n\n"
            f"💰 Amount: {amount}\n"
            f"💳 Method: {method}\n"
            f"🆔 Request ID: {withdrawal_id}\n\n"
            "Your request is waiting for admin approval."
        )

        # Admin notification
        if ADMIN_ID:

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Mark Paid",
                        callback_data=f"paid:{withdrawal_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"reject:{withdrawal_id}"
                    )
                ]
            ]

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "💳 NEW WITHDRAWAL\n\n"
                    f"🆔 Request: {withdrawal_id}\n"
                    f"👤 User: {user_id}\n"
                    f"💰 Amount: {amount}\n"
                    f"💳 Method: {method}\n"
                    f"📱 Account: {account}\n"
                    "📌 Status: Pending"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


# =========================
# ADMIN PAYMENT
# =========================

async def admin_paid(query, withdrawal_id):

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ Admin only.",
            show_alert=True
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT user_id, amount, status
        FROM withdrawals
        WHERE id=?
    """, (withdrawal_id,))

    row = cur.fetchone()

    if not row:
        con.close()

        await query.answer(
            "Request not found.",
            show_alert=True
        )
        return

    user_id, amount, status = row

    if status != "Pending":
        con.close()

        await query.answer(
            "This request is already processed.",
            show_alert=True
        )
        return

    cur.execute("""
        UPDATE withdrawals
        SET status='Paid'
        WHERE id=?
    """, (withdrawal_id,))

    con.commit()
    con.close()

    await query.edit_message_text(
        f"✅ Payment marked as PAID\n\n"
        f"Request ID: {withdrawal_id}\n"
        f"User: {user_id}\n"
        f"Amount: {amount}"
    )

    await context_bot_send(
        query,
        user_id,
        (
            "✅ Withdrawal Paid!\n\n"
            f"💰 Amount: {amount} coins\n"
            f"🆔 Request ID: {withdrawal_id}\n\n"
            "Your payment has been processed."
        )
    )


async def context_bot_send(query, user_id, text):

    try:
        await query.get_bot().send_message(
            chat_id=user_id,
            text=text
        )
    except Exception:
        pass


async def admin_reject(query, withdrawal_id):

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ Admin only.",
            show_alert=True
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT user_id, amount, status
        FROM withdrawals
        WHERE id=?
    """, (withdrawal_id,))

    row = cur.fetchone()

    if not row:
        con.close()

        await query.answer(
            "Request not found.",
            show_alert=True
        )
        return

    user_id, amount, status = row

    if status != "Pending":
        con.close()

        await query.answer(
            "Already processed.",
            show_alert=True
        )
        return

    # Return balance
    cur.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE user_id=?
    """, (amount, user_id))

    cur.execute("""
        UPDATE withdrawals
        SET status='Rejected'
        WHERE id=?
    """, (withdrawal_id,))

    con.commit()
    con.close()

    await query.edit_message_text(
        f"❌ Withdrawal rejected\n\n"
        f"Request ID: {withdrawal_id}\n"
        f"Amount returned: {amount}"
    )

    await context_bot_send(
        query,
        user_id,
        (
            "❌ Withdrawal Rejected\n\n"
            f"💰 {amount} coins returned to your balance.\n"
            f"🆔 Request ID: {withdrawal_id}"
        )
    )


# =========================
# CALLBACKS
# =========================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":

        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu()
        )

    elif data == "tasks":

        await show_tasks(query)

    elif data.startswith("complete:"):

        task_id = int(data.split(":")[1])

        await complete_task(
            query,
            task_id
        )

    elif data == "bonus":

        await daily_bonus(query)

    elif data == "invite":

        me = await context.bot.get_me()

        await invite(
            query,
            me.username
        )

    elif data == "balance":

        await balance(query)

    elif data == "withdraw":

        await withdraw_start(query)

    elif data.startswith("paid:"):

        withdrawal_id = int(data.split(":")[1])

        await admin_paid(
            query,
            withdrawal_id
        )

    elif data.startswith("reject:"):

        withdrawal_id = int(data.split(":")[1])

        await admin_reject(
            query,
            withdrawal_id
        )


# =========================
# ADMIN COMMANDS
# =========================

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 3:

        await update.message.reply_text(
            "Usage:\n"
            "/addtask Task_Name Reward Link\n\n"
            "Example:\n"
            "/addtask YouTube 20 https://youtube.com/"
        )
        return

    title = context.args[0]

    try:
        reward = int(context.args[1])
    except ValueError:

        await update.message.reply_text(
            "Reward must be a number."
        )
        return

    link = context.args[2]

    con = db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO tasks
        (title, reward, link, active)
        VALUES (?, ?, ?, 1)
    """, (title, reward, link))

    con.commit()
    con.close()

    await update.message.reply_text(
        "✅ Task added successfully!"
    )


async def admin_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "/adminbalance USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Invalid user ID."
        )
        return

    amount = get_balance(user_id)

    await update.message.reply_text(
        f"👤 User: {user_id}\n"
        f"💰 Balance: {amount}"
    )


# =========================
# RUN BOT
# ==================
