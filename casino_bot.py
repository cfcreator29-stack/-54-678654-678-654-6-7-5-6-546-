"""
🎰 Telegram Casino Bot — Multi-Win Edition
==========================================
Комбинации побед:
  777  (value=64) → 50 ⭐ звёзд
  🍋🍋🍋 (value=43) → мишка (стикер)
  🍇🍇🍇 (value=22) → мишка (стикер)
  BAR  (value=1)  → мишка (стикер)

Каждые 24 часа бот автоматически постит правила и призы в чат.

Установка:
    pip install pyTelegramBotAPI

Запуск:
    python casino_bot.py
"""

import telebot
import logging
import threading
import time
from datetime import datetime, timedelta
from telebot.types import Message

# ─────────────────────────────────────────────
#  НАСТРОЙКИ
# ─────────────────────────────────────────────

BOT_TOKEN       = "8760565363:AAEzaZx6beLq7mBu1YDrkRqOdSu-AtyEcAk"
ADMIN_ID        = 8535260202
ALLOWED_CHAT_ID = -1003771596513
PRIZE_STARS     = 50

# Стикер мишки — замени на реальный file_id своего стикера!
# Как узнать file_id: перешли стикер боту @getidsbot
BEAR_STICKER_FILE_ID = "CAACAgIAAxkBAAEBmj1mZ1AAAAAB"  # ← заменить!

# Время отправки правил каждый день (часы и минуты, UTC+3 Москва)
RULES_HOUR   = 10
RULES_MINUTE = 0

# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ─────────────────────────────────────────────
#  ТАБЛИЦА ВЫИГРЫШЕЙ
# ─────────────────────────────────────────────

WIN_TABLE = {
    64: {
        "label": "7️⃣7️⃣7️⃣ ДЖЕКПОТ",
        "type": "stars",
        "prize_text": f"{PRIZE_STARS} ⭐ звёзд",
        "emoji": "💰",
    },
    1: {
        "label": "🎰 BAR BAR BAR",
        "type": "bear",
        "prize_text": "плюшевый мишка 🧸",
        "emoji": "🧸",
    },
    22: {
        "label": "🍇🍇🍇 ВИНОГРАД",
        "type": "bear",
        "prize_text": "плюшевый мишка 🧸",
        "emoji": "🧸",
    },
    43: {
        "label": "🍋🍋🍋 ЛИМОН",
        "type": "bear",
        "prize_text": "плюшевый мишка 🧸",
        "emoji": "🧸",
    },
}


def get_win(value: int):
    return WIN_TABLE.get(value)


def get_mention(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = user.first_name
    if user.last_name:
        name += f" {user.last_name}"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


# ─────────────────────────────────────────────
#  ПРАВИЛА
# ─────────────────────────────────────────────

RULES_TEXT = (
    "🎰 <b>ПРАВИЛА КАЗИНО-БОТА</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Как играть:\n"
    "Отправь стикер 🎰 в этот чат и следи за результатом!\n\n"
    "🏆 <b>ТАБЛИЦА ПРИЗОВ:</b>\n\n"
    f"7️⃣7️⃣7️⃣  →  💰 <b>{PRIZE_STARS} ⭐ Звёзд</b>\n"
    "🍋🍋🍋  →  🧸 <b>Плюшевый мишка</b>\n"
    "🍇🍇🍇  →  🧸 <b>Плюшевый мишка</b>\n"
    "🎰 BAR  →  🧸 <b>Плюшевый мишка</b>\n\n"
    "📌 <b>Условия:</b>\n"
    "• Каждый может участвовать\n"
    "• Результат определяется случайно\n"
    "• При выигрыше напиши администратору\n\n"
    "🍀 <i>Удачи всем!</i>"
)


def post_rules():
    """Отправляет правила в чат и планирует следующую отправку через 24 ч."""
    try:
        bot.send_message(ALLOWED_CHAT_ID, RULES_TEXT)
        log.info("✅ Правила опубликованы в чат.")
    except Exception as e:
        log.error("Ошибка при отправке правил: %s", e)
    # Запланировать снова через 24 часа
    threading.Timer(24 * 60 * 60, post_rules).start()


def seconds_until_next_post():
    """Возвращает секунды до ближайшего RULES_HOUR:RULES_MINUTE."""
    now = datetime.now()
    target = now.replace(hour=RULES_HOUR, minute=RULES_MINUTE, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    diff = (target - now).total_seconds()
    return diff


def start_rules_scheduler():
    """Запускает таймер до первой отправки, потом каждые 24 ч."""
    delay = seconds_until_next_post()
    log.info(
        "⏰ Первая публикация правил через %.0f мин (в %02d:%02d).",
        delay / 60, RULES_HOUR, RULES_MINUTE,
    )

    def first_run():
        post_rules()  # post_rules сам планирует следующий запуск

    threading.Timer(delay, first_run).start()


# ─────────────────────────────────────────────
#  ОБРАБОТЧИК DICE
# ─────────────────────────────────────────────

@bot.message_handler(content_types=["dice"])
def handle_dice(message: Message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    if not (message.dice and message.dice.emoji == "🎰"):
        return

    value = message.dice.value
    log.info(
        "🎰 Dice от %s (id=%s): value=%s",
        message.from_user.username or message.from_user.first_name,
        message.from_user.id,
        value,
    )

    win = get_win(value)
    if not win:
        return

    mention = get_mention(message.from_user)
    user_id = message.from_user.id
    emoji   = win["emoji"]
    label   = win["label"]
    prize   = win["prize_text"]

    # Реакция 🎉
    try:
        bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[telebot.types.ReactionTypeEmoji("🎉")],
            is_big=True,
        )
    except Exception as e:
        log.warning("Реакция не установлена: %s", e)

    # Поздравление в чат
    bot.reply_to(
        message,
        f"{emoji} <b>{label}!</b>\n\n"
        f"🎉 Поздравляю, {mention}!\n"
        f"Ты выиграл <b>{prize}</b>!\n\n"
        f"Напиши администратору для получения приза 👇",
    )

    # Стикер мишки
    if win["type"] == "bear":
        try:
            bot.send_sticker(
                message.chat.id,
                BEAR_STICKER_FILE_ID,
                reply_to_message_id=message.message_id,
            )
        except Exception as e:
            log.warning("Не удалось отправить стикер мишки: %s", e)

    # Уведомление админу
    chat_id_link = str(message.chat.id).replace("-100", "")
    admin_text = (
        f"🏆 <b>Новый победитель!</b>\n\n"
        f"🎰 Комбинация: <b>{label}</b>\n"
        f"👤 Пользователь: {mention}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🎁 Приз: <b>{prize}</b>\n"
        f"🔗 <a href='https://t.me/c/{chat_id_link}/{message.message_id}'>Перейти к сообщению</a>"
    )
    try:
        bot.send_message(ADMIN_ID, admin_text, disable_web_page_preview=True)
    except Exception as e:
        log.error("Не удалось уведомить админа: %s", e)

    log.info("🏆 Победитель: %s (%s) — %s", mention, user_id, label)


# ─────────────────────────────────────────────
#  КОМАНДЫ
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start", "rules", "правила"])
def cmd_rules(message: Message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    bot.send_message(message.chat.id, RULES_TEXT)


# ─────────────────────────────────────────────
#  ЗАПУСК
# ─────────────────────────────────────────────

if __name__ == "__main__":
    start_rules_scheduler()
    log.info("🤖 Casino Bot запущен. Жду стикеры 🎰…")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
