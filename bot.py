import asyncio
from aiogram import Bot, Dispatcher, types
# (и весь остальной код)
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatMemberUpdated, ChatType
from aiogram.enums import ChatMemberStatus
import sqlite3
import os

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8220664661:AAEgzgF364BHjh6OLaHHoxUkCmekTILZMF8")
CHANNEL_LINK = "https://t.me/ERR0R_7O7"
DONATE_LINK = "https://nowpayments.io/payment/?api_key=HVZHGZD-ZXH4JN7-JTKJ21M-W7GKBZM"
BOT_USERNAME = "GypX_bot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === БАЗА ===
conn = sqlite3.connect("bot_data.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS settings (
    chat_id INTEGER PRIMARY KEY, 
    welcome TEXT, 
    rules TEXT, 
    warn_limit INTEGER DEFAULT 3, 
    warn_msg TEXT DEFAULT 'Ты получил варн')''')
c.execute('''CREATE TABLE IF NOT EXISTS warns (
    chat_id INTEGER, 
    user_id INTEGER, 
    count INTEGER, 
    PRIMARY KEY(chat_id, user_id))''')
conn.commit()

# === ПРИВЕТСТВИЕ ===
@dp.message(Command("setwelcome"))
async def set_welcome(msg: Message, command: CommandObject):
    if not msg.chat.type.endswith("group"): return
    if not msg.from_user.id in [admin.user.id for admin in await bot.get_chat_administrators(msg.chat.id)]: return
    welcome = command.args
    c.execute("INSERT OR REPLACE INTO settings (chat_id, welcome) VALUES (?, ?)", (msg.chat.id, welcome))
    conn.commit()
    await msg.reply("Приветствие записано, Мой Диктатор.")

@dp.message(Command("setrules"))
async def set_rules(msg: Message, command: CommandObject):
    if not msg.chat.type.endswith("group"): return
    if not msg.from_user.id in [admin.user.id for admin in await bot.get_chat_administrators(msg.chat.id)]: return
    rules = command.args
    c.execute("INSERT OR REPLACE INTO settings (chat_id, rules) VALUES (?, ?)", (msg.chat.id, rules))
    conn.commit()
    await msg.reply("Правила загружены. Надеюсь, кто-то их вообще читает.")

@dp.message(Command("welcome"))
async def get_welcome(msg: Message):
    c.execute("SELECT welcome FROM settings WHERE chat_id=?", (msg.chat.id,))
    res = c.fetchone()
    await msg.reply(res[0] if res else "Приветствие не установлено.")

@dp.message(Command("rules"))
async def get_rules(msg: Message):
    c.execute("SELECT rules FROM settings WHERE chat_id=?", (msg.chat.id,))
    res = c.fetchone()
    await msg.reply(res[0] if res else "Правила не заданы. Свобода? Или пиздец?")

# === ВАРНЫ ===
@dp.message(Command("setwarnlimit"))
async def set_warn_limit(msg: Message, command: CommandObject):
    if not msg.from_user.id in [admin.user.id for admin in await bot.get_chat_administrators(msg.chat.id)]: return
    c.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", (int(command.args), msg.chat.id))
    conn.commit()
    await msg.reply("Теперь банхаммер стучит после {} варнов.".format(command.args))

@dp.message(Command("setwarnmessage"))
async def set_warn_message(msg: Message, command: CommandObject):
    if not msg.from_user.id in [admin.user.id for admin in await bot.get_chat_administrators(msg.chat.id)]: return
    c.execute("UPDATE settings SET warn_msg=? WHERE chat_id=?", (command.args, msg.chat.id))
    conn.commit()
    await msg.reply("Варн будет сопровождаться мудростью: '{}'.".format(command.args))

@dp.message(Command("warn"))
async def warn_user(msg: Message):
    if not msg.reply_to_message: 
        return await msg.reply("Ответь на сообщение нарушителя, Мой Диктатор.")
    user_id = msg.reply_to_message.from_user.id
    chat_id = msg.chat.id
    c.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    row = c.fetchone()
    new_count = (row[0] + 1) if row else 1
    c.execute("INSERT OR REPLACE INTO warns (chat_id, user_id, count) VALUES (?, ?, ?)", (chat_id, user_id, new_count))
    conn.commit()
    c.execute("SELECT warn_limit, warn_msg FROM settings WHERE chat_id=?", (chat_id,))
    setting = c.fetchone() or (3, "Ты получил варн")
    await msg.reply(f"{setting[1]} ({new_count}/{setting[0]})")
    if new_count >= setting[0]:
        await msg.reply("Пошёл нах!")
        await bot.ban_chat_member(chat_id, user_id)
        c.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        conn.commit()

# === ИГРА ===
@dp.message(Command("coinflip"))
async def coinflip(msg: Message):
    from random import choice
    await msg.reply(f"{msg.from_user.first_name}, тебе выпало: {choice(['Орел 🦅', 'Решка 🪙'])}. Фортуна тебя терпит.")

# === ПРИ ДОБАВЛЕНИИ В ГРУППУ ===
@dp.chat_member()
async def on_chat_join(event: ChatMemberUpdated):
    if event.new_chat_member.status == ChatMemberStatus.MEMBER and event.from_user.id == bot.id:
        admins = await bot.get_chat_administrators(event.chat.id)
        for admin in admins:
            try:
                await bot.send_message(admin.user.id,
                    f"📌 Справка для Админов\n\nЯ GypX Bot. Не Ирис, но дерзкий.\n\n🛠 Команды:\n/setwelcome — приветствие\n/setrules — правила\n/setwarnlimit — лимит варнов\n/setwarnmessage — текст при варне\n/warn — выдать варн\n/coinflip — орёл/решка\n\n📚 Подробнее:\n👉 https://t.me/{BOT_USERNAME}?start=about\n💸 Донат: {DONATE_LINK}\n📢 Канал: {CHANNEL_LINK}\n\n⚠️ Без админки я мебель. С админкой — судья.")
            except:
                pass

# === СПРАВКА /start ===
@dp.message(Command("start"))
async def start(msg: Message, command: CommandObject):
    if command.args == "about":
        await msg.reply(f"📌 GypX Bot. Помощник из-за жалости.\n\n/setwelcome — установить приветствие\n/setrules — установить правила\n/setwarnlimit — лимит варнов\n/setwarnmessage — сообщение при варне\n/warn — выдать варн (по ответу на сообщение)\n/coinflip — орёл или решка\n/rules — показать правила\n/welcome — показать приветствие\n\n💸 Донат: {DONATE_LINK}\n📢 Новости: {CHANNEL_LINK}")

# === ЗАПУСК ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
