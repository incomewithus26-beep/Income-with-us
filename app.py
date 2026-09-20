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

BOT_USERNAME = "incomewithus26bot"
REFERRAL_REWARD = 5

DB = "bot.db"


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER
        )
    """)

    conn.commit()
    conn.close()


def create_user(user_id, referred_by=None):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO users "
        "(user_id, referred_by) VALUES (?, ?)",
        (user_id, referred_by)
    )

    conn.commit()
    conn.close()


def get_balance(user_id):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result[0] if result else 0


def get_referrals(user_id):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT referrals FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result[0] if result else 0


def add_balance(user_id, amount):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET balance = balance + ? "
        "WHERE user_id = ?",
        (amount, user_id)
    )

    conn.commit()
    conn.close()


def add_referral(user_id):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET referrals = referrals + 1, "
        "balance = balance + ? "
        "WHERE user_id = ?",
        (REFERRAL_REWARD, user_id)
    )

    conn.commit()
    conn.close()


# =========================
# REFERRAL CHECK
# =========================

def user_exists(user_id):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result is not None


def referral_already_used(user_id):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT referred_by FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    if result and result[0]:
        return True

    return False


# =========================
# MAIN MENU
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn"
            ),
            InlineKeyboardButton(
                "🎁 Bonus",
                callback_data="bonus"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 Invite & Earn",
                callback_data="invite"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "💳 Withdraw",
                callback_data="withdraw"
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data="settings"
            ),
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # Referral ID
    referred_by = None

    if context.args:

        try:
            ref_id = int(context.args[0])

            # নিজেকে referral করা যাবে না
            if ref_id != user_id:

                # Referrer অবশ্যই আগে থেকে user হতে হবে
                if user_exists(ref_id):

                    referred_by = ref_id

        except ValueError:
            pass

    # নতুন user
    if not user_exists(user_id):

        create_user(user_id, referred_by)

        # Valid referral হলে referrer reward পাবে
        if referred_by:

            add_referral(referred_by)

    else:

        create_user(user_id)

    await update.message.reply_text(
        "👋 Welcome to Income With Me!\n\n"
        "💰 Earn from available legitimate tasks.\n"
        "👥 Invite friends and earn referral rewards.\n"
        "📊 Check your balance anytime.\n\n"
        "👇 Choose an option:",
        reply_markup=main_menu()
    )


# =========================
# EARN
# =========================

async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Task #1 — Earn ৳5",
                callback_data="task_1"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="home"
            )
        ]
    ]

    await update.message.reply_text(
        "💰 Earn Section\n\n"
        "📝 Task #1\n"
        "💵 Reward: ৳5\n\n"
        "Complete the legitimate task according to "
        "the instructions.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BONUS
# =========================

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 Daily Bonus",
                callback_data="daily_bonus"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="home"
            )
        ]
    ]

    await update.message.reply_text(
        "🎁 Bonus Section",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BALANCE
# =========================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    amount = get_balance(user_id)
    referrals = get_referrals(user_id)

    keyboard = [
        [
            InlineKeyboardButton(
                "👥 Invite",
                callback_data="invite"
            )
        ],
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
    ]

    await update.message.reply_text(
        f"📊 Your Balance\n\n"
        f"💰 Balance: ৳{amount:.2f}\n"
        f"👥 Referrals: {referrals}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# WITHDRAW
# =========================

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    amount = get_balance(user_id)

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="home"
            )
        ]
    ]

    await update.message.reply_text(
        f"💳 Withdraw\n\n"
        f"Current Balance: ৳{amount:.2f}\n\n"
        "⚠️ Withdrawal system is not active yet.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    create_user(user_id)

    # =========================
    # HOME
    # =========================

    if query.data == "home":

        await query.edit_message_text(
            "🏠 Main Menu\n\n"
            "👇 Choose an option:",
            reply_markup=main_menu()
        )

    # =========================
    # INVITE
    # =========================

    elif query.data == "invite":

        referrals = get_referrals(user_id)
        balance_amount = get_balance(user_id)

        referral_link = (
            f"https://t.me/{BOT_USERNAME}"
            f"?start={user_id}"
        )

        share_text = (
            "Join Income With Me and check available "
            "earning opportunities!"
        )

        share_url = (
            "https://t.me/share/url?"
            f"url={referral_link}"
            f"&text={share_text}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📤 Share Invite Link",
                    url=share_url
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
            "👥 Invite & Earn\n\n"
            f"🔗 Your Referral Link:\n"
            f"{referral_link}\n\n"
            f"👤 Total Referrals: {referrals}\n"
            f"💰 Referral Reward: ৳{REFERRAL_REWARD}\n"
            f"📊 Your Balance: ৳{balance_amount:.2f}\n\n"
            "Share your link with friends.\n"
            "A referral is counted only when a new user "
            "joins through your link.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # EARN
    # =========================

    elif query.data == "earn":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Task #1 — Earn ৳5",
                    callback_data="task_1"
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
            "💰 Earn Section\n\n"
            "📝 Task #1\n"
            "💵 Reward: ৳5",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # TASK
    # =========================

    elif query.data == "task_1":

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Complete Task",
                    callback_data="complete_1"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Earn",
                    callback_data="earn"
                )
            ]
        ]

        await query.edit_message_text(
            "📝 Task #1\n\n"
            "Complete the legitimate task "
            "according to the instructions.\n\n"
            "💵 Reward: ৳5",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # BONUS
    # =========================

    elif query.data == "bonus":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎁 Daily Bonus",
                    callback_data="daily_bonus"
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
            "🎁 Bonus Section",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # DAILY BONUS
    # =========================

    elif query.data == "daily_bonus":

        await query.edit_message_text(
            "🎁 Daily Bonus\n\n"
            "Daily bonus system will be configured later."
        )

    # =========================
    # BALANCE
    # =========================

    elif query.data == "balance":

        amount = get_balance(user_id)
        referrals = get_referrals(user_id)

        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Invite",
                    callback_data="invite"
                )
            ],
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
        ]

        await query.edit_message_text(
            f"📊 Your Balance\n\n"
            f"💰 Balance: ৳{amount:.2f}\n"
            f"👥 Referrals: {referrals}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # WITHDRAW
    # =========================

    elif query.data == "withdraw":

        amount = get_balance(user_id)

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            f"💳 Withdraw\n\n"
            f"Balance: ৳{amount:.2f}\n\n"
            "⚠️ Withdrawal system is not active yet.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # SETTINGS
    # =========================

    elif query.data == "settings":

        keyboard = [
            [
                InlineKeyboardButton(
                    "👤 Profile",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔔 Notifications",
                    callback_data="notifications"
                )
            ],
            [
                InlineKeyboardButton(
                    "🌐 Language",
                    callback_data="language"
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
            "⚙️ Settings\n\n"
            "Choose a setting:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # PROFILE
    # =========================

    elif query.data == "profile":

        user = query.from_user

        username = (
            f"@{user.username}"
            if user.username
            else "Not set"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Settings",
                    callback_data="settings"
                )
            ]
        ]

        await query.edit_message_text(
            f"👤 Profile\n\n"
            f"Name: {user.first_name}\n"
            f"Username: {username}\n"
            f"User ID: {user.id}\n"
            f"Balance: ৳{get_balance(user_id):.2f}\n"
            f"Referrals: {get_referrals(user_id)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # HELP
    # =========================

    elif query.data == "help":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🤖 How to Use",
                    callback_data="how_to_use"
                )
            ],
            [
                InlineKeyboardButton(
                    "💰 How to Earn",
                    callback_data="how_to_earn"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 Invite Help",
                    callback_data="invite_help"
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Withdraw Help",
                    callback_data="withdraw_help"
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
            "❓ Help Center",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # INVITE HELP
    # =========================

    elif query.data == "invite_help":

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Help",
                    callback_data="help"
                )
            ]
        ]

        await query.edit_message_text(
            "👥 Invite & Earn Help\n\n"
            "1️⃣ Open Invite & Earn\n"
            "2️⃣ Copy or share your referral link\n"
            "3️⃣ A new user joins through your link\n"
            "4️⃣ The valid referral is counted\n\n"
            f"💰 Demo referral reward: ৳{REFERRAL_REWARD}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # OTHER HELP
    # =========================

    elif query.data == "how_to_use":

        await query.edit_message_text(
            "🤖 How to Use\n\n"
            "Open the menu and select the feature "
            "you want to use."
        )

    elif query.data == "how_to_earn":

        await query.edit_message_text(
            "💰 How to Earn\n\n"
            "Complete legitimate tasks available "
            "inside the bot.\n\n"
            "⚠️ Earnings are not guaranteed."
        )

    elif query.data == "withdraw_help":

        await query.edit_message_text(
            "💳 Withdraw Help\n\n"
            "Withdrawal system is currently being configured."
        )

    # =========================
    # SETTINGS BUTTONS
    # =========================

    elif query.data == "notifications":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔔 ON",
                    callback_data="notification_on"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔕 OFF",
                    callback_data="notification_off"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Settings",
                    callback_data="settings"
                )
            ]
        ]

        await query.edit_message_text(
            "🔔 Notifications\n\n"
            "Choose notification setting:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "notification_on":

        await query.edit_message_text(
            "🔔 Notifications: ON"
        )

    elif query.data == "notification_off":

        await query.edit_message_text(
            "🔕 Notifications: OFF"
        )

    elif query.data == "language":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🇧🇩 বাংলা",
                    callback_data="bangla"
                )
            ],
            [
                InlineKeyboardButton(
                    "🇬🇧 English",
                    callback_data="english"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Settings",
                    callback_data="settings"
                )
            ]
        ]

        await query.edit_message_text(
            "🌐 Language\n\n"
            "Select language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "bangla":

        await query.edit_message_text(
            "🇧🇩 Language: বাংলা"
        )

    elif query.data == "english":

        await query.edit_message_text(
            "🇬🇧 Language: English"
        )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN is missing. "
            "Add BOT_TOKEN in Render Environment Variables."
        )

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("earn", earn)
    )

    app.add_handler(
        CommandHandler("bonus", bonus)
    )

    app.add_handler(
        CommandHandler("balance", balance)
    )

    app.add_handler(
        CommandHandler("withdraw", withdraw)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("🤖 Income With Me Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
