import json
import os
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"
user_pushup_state = {}  # user_id -> ожидается ввод числа отжиманий

# Кнопки привычек
def habit_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Контрастный душ"))
    kb.add(KeyboardButton("Чтение"))
    kb.add(KeyboardButton("Витамины"))
    kb.add(KeyboardButton("100 отжиманий"))
    return kb

# Работа с JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_user(data, user_id):
    if str(user_id) not in data:
        data[str(user_id)] = {
            "Контрастный душ": {"streak": 0, "last_done": None},
            "Чтение": {"streak": 0, "last_done": None},
            "Витамины": {"streak": 0, "last_done": None},
            "100 отжиманий": {"streak": 0, "last_done": None, "progress": 0}
        }

def mark_habit_done(data, user_id, habit):
    today = datetime.date.today().isoformat()
    user = data[str(user_id)][habit]
    last = user["last_done"]
    if last != today:
        if last == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
            user["streak"] += 1
        else:
            user["streak"] = 1
        user["last_done"] = today
    return user["streak"]

def add_pushups(data, user_id, count):
    today = datetime.date.today().isoformat()
    user = data[str(user_id)]["100 отжиманий"]
    last = user["last_done"]
    if last != today:
        if last == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
            user["streak"] += 1
        else:
            user["streak"] = 0
        user["progress"] = 0
        user["last_done"] = today
    user["progress"] += count
    done = user["progress"] >= 100
    remaining = max(0, 100 - user["progress"])
    return remaining, done, user["streak"]

@dp.message(Command("start"))
async def start(message: types.Message):
    data = load_data()
    init_user(data, message.from_user.id)
    save_data(data)
    await message.answer("Привет! Я твой трекер привычек.", reply_markup=habit_keyboard())

@dp.message()
async def handle_habit(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    data = load_data()
    init_user(data, user_id)

    if text in ["Контрастный душ", "Чтение", "Витамины"]:
        streak = mark_habit_done(data, user_id, text)
        save_data(data)
        await message.answer(f"✅ '{text}' засчитано! Текущий рекорд дней подряд: {streak}")
    
    elif text == "100 отжиманий":
        user_pushup_state[user_id] = True
        await message.answer("Сколько отжиманий сделал? Вводи число.")
    
    elif user_pushup_state.get(user_id):
        if text.isdigit():
            count = int(text)
            remaining, done, streak = add_pushups(data, user_id, count)
            save_data(data)
            if done:
                await message.answer(f"💪 Отлично! 100 отжиманий выполнены. Счетчик дней подряд: {streak}")
            else:
                await message.answer(f"Сделано {count}. Осталось {remaining}. Продолжай!")
        else:
            await message.answer("Пожалуйста, введи число отжиманий.")
    else:
        await message.answer("Выбери привычку из кнопок ниже.", reply_markup=habit_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
