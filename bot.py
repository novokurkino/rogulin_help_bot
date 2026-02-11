import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import date, timedelta

# -----------------------------
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN не найден! Добавь его в Variables на Railway.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# -----------------------------
# FSM для ввода отжиманий
class PushupState(StatesGroup):
    waiting_for_count = State()

# -----------------------------
# Пользовательские данные
user_data = {}  # структура: {user_id: {habit_name: count, pushups_done: int, streak: int, last_date: date}}

HABITS = ["Контрастный душ", "Чтение", "Витамины", "100 отжиманий"]

# -----------------------------
# Создаем клавиатуру с привычками
def habit_keyboard(user_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    for habit in HABITS:
        kb.add(InlineKeyboardButton(text=habit, callback_data=f"habit:{habit}"))
    return kb

# -----------------------------
# Команда /start
@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            "Контрастный душ": 0,
            "Чтение": 0,
            "Витамины": 0,
            "100 отжиманий": 0,
            "streak": 0,
            "last_pushup_date": None,
            "last_reset": date.today()
        }
    await message.answer("Привет! Вот твой трекер привычек на сегодня:", reply_markup=habit_keyboard(user_id))

# -----------------------------
# Обработка нажатий на кнопки
@dp.callback_query(lambda c: c.data and c.data.startswith("habit:"))
async def habit_pressed(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    habit = callback.data.split(":")[1]

    today = date.today()
    data = user_data[user_id]

    # Сброс дневных счетчиков если новый день
    if data.get("last_reset") != today:
        data["Контрастный душ"] = 0
        data["Чтение"] = 0
        data["Витамины"] = 0
        data["100 отжиманий"] = 0
        data["last_reset"] = today
        await callback.message.answer("Новый день! Счетчики привычек сброшены.")

    if habit != "100 отжиманий":
        if data[habit] == 0:
            data[habit] = 1
            await callback.message.answer(f"Привычка '{habit}' выполнена ✅")
        else:
            await callback.message.answer(f"Привычка '{habit}' уже выполнена сегодня!")
    else:
        await callback.message.answer("Сколько отжиманий сделал? Введи число:")
        await state.set_state(PushupState.waiting_for_count)

    await callback.answer()

# -----------------------------
# Обработка ввода числа отжиманий
@dp.message(PushupState.waiting_for_count)
async def pushup_count(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = user_data[user_id]

    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное число отжиманий!")
        return

    # Проверяем дату для streak
    today = date.today()
    if data.get("last_pushup_date") == today - timedelta(days=1):
        data["streak"] += 1
    elif data.get("last_pushup_date") != today:
        data["streak"] = 1  # сброс, если пропустил день

    data["100 отжиманий"] += count
    data["last_pushup_date"] = today

    remaining = max(0, 100 - data["100 отжиманий"])
    if remaining > 0:
        await message.answer(f"Ты сделал {data['100 отжиманий']} отжиманий. Осталось {remaining} 🏋️")
    else:
        await message.answer(f"Дневной план отжиманий выполнен! 🎉\nТекущий непрерывный стрик: {data['streak']} дней")
        data["100 отжиманий"] = 100  # фиксируем максимум

    await state.clear()

# -----------------------------
# Команда /status - показать текущее состояние
@dp.message(Command(commands=["status"]))
async def status(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)
    if not data:
        await message.answer("Нет данных. Нажми /start")
        return

    text = (
        f"Твои привычки на сегодня:\n"
        f"Контрастный душ: {'✅' if data['Контрастный душ'] else '❌'}\n"
        f"Чтение: {'✅' if data['Чтение'] else '❌'}\n"
        f"Витамины: {'✅' if data['Витамины'] else '❌'}\n"
        f"100 отжиманий: {data['100 отжиманий']}/100\n"
        f"Стрик дней с отжиманиями: {data['streak']}"
    )
    await message.answer(text)

# -----------------------------
# Запуск бота
if __name__ == "__main__":
    import asyncio
    print("Бот запущен...")
    asyncio.run(dp.start_polling(bot))
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Получаем токен из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("API_TOKEN не найден! Добавь его в Variables на Railway.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
