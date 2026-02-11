import json
import datetime
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

API_TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"
DATA_FILE = "users_data.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== Загрузка данных ==================
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users_data = json.load(f)
except FileNotFoundError:
    users_data = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

# ================== Кнопки ==================
def main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Контрастный душ", callback_data="habit_shower"),
        InlineKeyboardButton("Чтение", callback_data="habit_reading"),
        InlineKeyboardButton("Витамины", callback_data="habit_vitamins"),
        InlineKeyboardButton("100 отжиманий", callback_data="habit_pushups"),
        InlineKeyboardButton("Проверить все привычки", callback_data="check_all")
    )
    return keyboard

# ================== Старт ==================
@dp.message()
async def start(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {}
        save_data()
    await message.answer(
        "Привет! Это твой трекер привычек.\nВыбирай привычку для отметки сегодня:",
        reply_markup=main_keyboard()
    )

# ================== Обработка привычек ==================
@dp.callback_query()
async def habit_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    habit = call.data.replace("habit_", "")
    today = datetime.date.today().isoformat()

    if str(user_id) not in users_data:
        users_data[str(user_id)] = {}
    user = users_data[str(user_id)]

    if habit == "pushups":
        await call.message.answer("Сколько отжиманий ты сделал сегодня?")
        user["await_pushups"] = True
        users_data[str(user_id)] = user
        save_data()
        await call.answer()
        return

    if habit == "check_all":
        if not user:
            await call.message.answer("Ты ещё не отмечал ни одну привычку.")
        else:
            text = "Твои привычки и дни подряд:\n"
            for h, data in user.items():
                if h != "await_pushups":
                    text += f"- {h.replace('_',' ')}: {data.get('streak',0)} дней подряд\n"
            await call.message.answer(text)
        await call.answer()
        return

    habit_data = user.get(habit, {"last_date": None, "streak": 0})
    last_date = habit_data["last_date"]
    streak = habit_data["streak"]

    if last_date != today:
        if last_date is not None:
            last_date_dt = datetime.date.fromisoformat(last_date)
            if (datetime.date.today() - last_date_dt).days > 1:
                streak = 0
        streak += 1
        habit_data["streak"] = streak
        habit_data["last_date"] = today
        user[habit] = habit_data
        users_data[str(user_id)] = user
        save_data()
        await call.message.answer(f"Привычка '{habit.replace('_',' ')}' засчитана!\nДней подряд: {streak}")
    else:
        await call.message.answer(f"Ты уже отмечал эту привычку сегодня!\nДней подряд: {streak}")

    await call.answer()

# ================== Отжимания ==================
@dp.message()
async def pushups_input(message: types.Message):
    user_id = message.from_user.id
    user = users_data.get(str(user_id), {})

    if not user.get("await_pushups"):
        return

    today = datetime.date.today().isoformat()
    
    try:
        count = int(message.text)
        if count <= 0:
            await message.answer("Введите положительное число.")
            return
    except ValueError:
        await message.answer("Введите число отжиманий цифрой.")
        return

    habit = "pushups"
    habit_data = user.get(habit, {"last_date": None, "streak": 0, "done": 0})
    last_date = habit_data.get("last_date")
    streak = habit_data.get("streak", 0)
    done = habit_data.get("done", 0)

    if last_date != today:
        if last_date is not None:
            last_date_dt = datetime.date.fromisoformat(last_date)
            if (datetime.date.today() - last_date_dt).days > 1:
                streak = 0
        done = 0
        streak += 1

    done += count
    habit_data["done"] = done
    habit_data["last_date"] = today
    habit_data["streak"] = streak

    user[habit] = habit_data
    user.pop("await_pushups", None)
    users_data[str(user_id)] = user
    save_data()

    if done >= 100:
        await message.answer(f"Отлично! Ты сделал 100 отжиманий! Дней подряд: {streak}")
        habit_data["done"] = 100
        user[habit] = habit_data
        users_data[str(user_id)] = user
        save_data()
    else:
        await message.answer(f"Сделано {done} из 100 отжиманий. Осталось {100 - done}.")

    await message.answer("Выбирай следующую привычку:", reply_markup=main_keyboard())

# ================== Запуск ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
