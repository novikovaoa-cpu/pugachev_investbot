import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7431209440:AAGg_jFe9L9Ga_pef2z6wyV3p2MIpMuMLzc"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Form(StatesGroup):
    answering = State()


QUESTIONS = [
    {"id": 1, "text": "1. Каков Ваш текущий возраст?", "options": [("18-29 лет", 5), ("30-39 лет", 4), ("40-49 лет", 3), ("50-59 лет", 2), ("59+", 1)]},
    {"id": 2, "text": "2. Сколько людей зависят от Вас?", "options": [("0", 5), ("1", 4), ("2", 3), ("3", 2), ("4+", 1)]},
    {"id": 3, "text": "3. Есть ли недвижимость?", "options": [("Без ипотеки", 5), ("Аренда", 2), ("Ипотека <50%", 4), ("Ипотека >50%", 2), ("Отрицательная стоимость", 1)]},
    {"id": 4, "text": "4. Опыт инвестирования?", "options": [("Эксперт", 5), ("Есть опыт", 4), ("Мало опыта", 2), ("Нет опыта", 1)]},
    {"id": 5, "text": "5. Готовность к риску?", "options": [("Максимальная", 5), ("Высокая", 4), ("Средняя", 3), ("Низкая", 2), ("Минимальная", 1)]},
    {"id": 6, "text": "6. Инвест цель?", "options": [("Макс рост", 5), ("Баланс", 4), ("Чуть выше депозита", 3), ("Сохранить", 1)]},
    {"id": 7, "text": "7. Горизонт инвестиций?", "options": [("1-5 лет", 1), ("5-10", 2), ("10-15", 3), ("15-20", 4), ("20+", 5)]},
    {"id": 8, "text": "8. Допустимая просадка?", "options": [("85%", 5), ("45%", 4), ("25%", 3), ("10%", 2), ("5%", 1)]},
    {"id": 9, "text": "9. Сумма инвестиций?", "options": [("150k+", 5), ("100k", 4), ("50k", 3), ("20k", 2), ("до 20k", 1)]},
    {"id": 10, "text": "10. Уверенность в решениях?", "options": [("Полная", 5), ("Высокая", 4), ("Средняя", 3), ("Низкая", 2), ("Нет", 1)]},
    {"id": 11, "text": "11. Резервный фонд?", "options": [("Нет", 1), ("<3 мес", 2), ("Есть", 5)]},
    {"id": 12, "text": "12. Когда пассивный доход?", "options": [("5-10 лет", 2), ("10-20", 3), ("20-30", 4), ("30+", 5)]},
    {"id": 13, "text": "13. Дельта доходов?", "options": [("0", 1), ("100-300$", 2), ("300-500$", 3), ("500-1000$", 4), ("1000+$", 5)]},
    {"id": 14, "text": "14. Кто влияет?", "options": [("Сам", 5), ("Супруг", 3), ("Другие", 2)]},
    {"id": 15, "text": "15. Есть долги?", "options": [("Нет", 5), ("Да", 2)]},
]


def calculate_result(answers):

    def avg(ids):
        return sum(answers.get(i, 1) for i in ids) / len(ids)

    risk = avg([5, 8, 10])
    horizon = avg([1, 7, 12])
    finance = avg([2, 3, 11, 13, 15])
    experience = avg([4, 6, 9, 14])

    def norm(x):
        return (x - 1) / 4 * 100

    risk = norm(risk)
    horizon = norm(horizon)
    finance = norm(finance)
    experience = norm(experience)

    final = risk * 0.4 + horizon * 0.25 + finance * 0.2 + experience * 0.15

    if risk < 30:
        profile = "Консервативный"
    elif final < 40:
        profile = "Консервативный"
    elif final < 70:
        profile = "Сбалансированный"
    else:
        profile = "Агрессивный"

    return profile, round(final, 2), {
        "Риск": round(risk, 1),
        "Горизонт": round(horizon, 1),
        "Финансы": round(finance, 1),
        "Опыт": round(experience, 1),
    }


def get_kb(i):
    kb = InlineKeyboardBuilder()
    for t, s in QUESTIONS[i]["options"]:
        kb.button(text=t, callback_data=f"a:{i}:{s}")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.set_state(Form.answering)
    await state.update_data(i=0, answers={})
    await m.answer("Начинаем тест")
    await m.answer(QUESTIONS[0]["text"], reply_markup=get_kb(0))


@dp.callback_query(F.data.startswith("a:"), Form.answering)
async def answer(c: CallbackQuery, state: FSMContext):
    await c.answer()

    _, i, s = c.data.split(":")
    i = int(i)
    s = int(s)

    data = await state.get_data()
    answers = data["answers"]
    answers[QUESTIONS[i]["id"]] = s

    i += 1
    await state.update_data(i=i, answers=answers)

    if i < len(QUESTIONS):
        await c.message.answer(QUESTIONS[i]["text"], reply_markup=get_kb(i))
    else:
        profile, final, breakdown = calculate_result(answers)

        text = f"""
Ваш риск-профиль: {profile}

Итоговый балл: {final}/100

Разбор:
— Риск: {breakdown['Риск']}
— Горизонт: {breakdown['Горизонт']}
— Финансы: {breakdown['Финансы']}
— Опыт: {breakdown['Опыт']}
"""
        await c.message.answer(text)
        await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    