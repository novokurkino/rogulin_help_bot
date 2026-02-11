import json
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

# ================== Настройки ==================
API_TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"  # <-- Вставьте свой токен
DATA_FILE = "users_data.json"

# ================== Инициализация ==================
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================== Загрузка данных ==================
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users_data = json.load(f)
except FileNotFoundError:
    users_data = {}

# ================== Сохранение данных ==================
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
        InlineKeyboardButton("100 отжиманий", callback_data="habit_pushups")
    )
    return keyboard

# ================== Помощь с днями ==================
def check_streak(user_id, habit):
    today = datetime.date.today().isoformat()
    user = users_data.get(str(user_id), {})
    habit_data = user.get(habit, {"last_date": None, "streak": 0})

    last_date = habit_data["last_date"]
    streak = habit_data["streak"]

    if last_date != today:
        if last_date is not None:
            last_date_dt = datetime.date.fromisoformat(last_date)
            if (datetime.date.today() - last_date_dt).days > 1:
                streak = 0  # сброс при пропуске дня
        habit_data["streak"] = streak
    user[habit] = habit_data
    users_data[str(user_id)] = user
    save_data()
    return streak

# ================== Хендлеры ==================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {}
        save_data()
    await message.answer(
        "Привет! Это твой трекер привычек.\nВыбирай привычку для отметки сегодня:",
        reply_markup=main_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("habit_"))
async def habit_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    habit = call.data.replace("habit_", "")
    today = datetime.date.today().isoformat()

    if str(user_id) not in users_data:
        users_data[str(user_id)] = {}

    user = users_data[str(user_id)]

    # ================== Отжимания ==================
    if habit == "pushups":
        await call.message.answer("Сколько отжиманий ты сделал сегодня?")
        # Сохраняем, что сейчас пользователь вводит число для отжиманий
        user["await_pushups"] = True
        users_data[str(user_id)] = user
        save_data()
        await call.answer()
        return

    # ================== Привычки ==================
    habit_data = user.get(habit, {"last_date": None, "streak": 0})
    last_date = habit_data["last_date"]
    streak = habit_data["streak"]

    if last_date != today:
        # Проверка на пропуск
        if last_date is not None:
            last_date_dt = datetime.date.fromisoformat(last_date)
            if (datetime.date.today() - last_date_dt).days > 1:
                streak = 0  # сброс
        streak += 1
        habit_data["streak"] = streak
        habit_data["last_date"] = today
        user[habit] = habit_data
        users_data[str(user_id)] = user
        save_data()

        await call.message.answer(f"Привычка '{habit.replace('_', ' ')}' засчитана!\nДней подряд: {streak}")
    else:
        await call.message.answer(f"Ты уже отмечал эту привычку сегодня!\nДней подряд: {streak}")
    await call.answer()

@dp.message_handler(lambda m: str(m.from_user.id) in users_data and users_data[str(m.from_user.id)].get("await_pushups"))
async def pushups_input(message: types.Message):
    user_id = message.from_user.id
    user = users_data[str(user_id)]
    today = datetime.date.today().isoformat()
    
    try:
        count = int(message.text)
        if count <= 0:
            await message.answer("Введите положительное число.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число отжиманий цифрой.")
        return

    # Получаем данные отжиманий
    habit = "pushups"
    habit_data = user.get(habit, {"last_date": None, "streak": 0, "done": 0})
    last_date = habit_data.get("last_date")
    streak = habit_data.get("streak", 0)
    done = habit_data.get("done", 0)

    # Проверка на новый день
    if last_date != today:
        if last_date is not None:
            last_date_dt = datetime.date.fromisoformat(last_date)
            if (datetime.date.today() - last_date_dt).days > 1:
                streak = 0  # сброс
        done = 0  # новый день
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
        await message.answer(f"Отлично! Ты сделал 100 отжиманий. План дня выполнен!\nДней подряд: {streak}")
        habit_data["done"] = 100
        user[habit] = habit_data
        users_data[str(user_id)] = user
        save_data()
    else:
        await message.answer(f"Сделано {done} из 100 отжиманий. Осталось {100 - done}.")
    
    await message.answer("Выбирай следующую привычку:", reply_markup=main_keyboard())

# ================== Запуск ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
