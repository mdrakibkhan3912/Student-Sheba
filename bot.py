import os
import requests
import asyncio
import threading

from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================
# BOT TOKEN
# ============================================

BOT_TOKEN = "8731172921:AAEHx3x7_RiK8rHrV6lOe0YmmS7iq1HSnjs"

# ============================================
# ADMIN IDS
# ============================================

ADMIN_IDS = [
    6938462920
]

# ============================================
# FLASK KEEP ALIVE
# ============================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# ============================================
# AIROGRAM
# ============================================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(storage=MemoryStorage())

# ============================================
# STATES
# ============================================

class StudentState(StatesGroup):

    waiting_for_eiin = State()

    waiting_for_student = State()

# ============================================
# BUTTONS
# ============================================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="EIIN Number")
        ]
    ],
    resize_keyboard=True
)

# ============================================
# STUDENT API
# ============================================

def check_student(student_id, institute_id):

    url = "https://api.shebashikkha.com/public/student-portal/login"

    params = {
        "customStudentId": student_id,
        "instituteId": institute_id
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )

        data = r.json()

        if data.get("messageType") == 1:

            item = data.get("item", {})

            return {
                "valid": True,

                "student_id": item.get("customStudentId"),

                "name": item.get("studentName"),

                "father": item.get("fatherName"),

                "mother": item.get("motherName"),

                "mobile": item.get("guardianMobile"),

                "gender": item.get("studentGender"),

                "class": item.get("className"),

                "group": item.get("groupName"),

                "section": item.get("sectionName"),

                "roll": item.get("studentRoll"),

                "institute": item.get("instituteName"),
            }

        return {
            "valid": False
        }

    except:

        return {
            "valid": False
        }

# ============================================
# START
# ============================================

@dp.message(CommandStart())
async def start(message: Message):

    if message.from_user.id not in ADMIN_IDS:

        await message.answer(
            "Access denied"
        )

        return

    await message.answer(
        "✅ Welcome To Student Lookup Bot",
        reply_markup=main_keyboard
    )

# ============================================
# EIIN BUTTON
# ============================================

@dp.message(F.text == "EIIN Number")
async def eiin_button(message: Message, state: FSMContext):

    await message.answer(
        "📚 Send Institute EIIN Number"
    )

    await state.set_state(
        StudentState.waiting_for_eiin
    )

# ============================================
# SAVE EIIN
# ============================================

@dp.message(StudentState.waiting_for_eiin)
async def save_eiin(message: Message, state: FSMContext):

    eiin = message.text.strip()

    await state.update_data(
        eiin=eiin
    )

    await message.answer(
        f"✅ Institute Saved: {eiin}\n\n"
        f"Now Send Student ID OR Range\n\n"
        f"Example:\n"
        f"2010765901\n\n"
        f"OR\n\n"
        f"2010765901-2010766000"
    )

    await state.set_state(
        StudentState.waiting_for_student
    )

# ============================================
# SEARCH SYSTEM
# ============================================

@dp.message(StudentState.waiting_for_student)
async def search_student(message: Message, state: FSMContext):

    text_input = message.text.strip()

    data = await state.get_data()

    eiin = data.get("eiin")

    if not eiin:

        await message.answer(
            "❌ First Set EIIN Number"
        )

        return

    # ========================================
    # RANGE SEARCH
    # ========================================

    if "-" in text_input:

        try:

            start, end = map(
                int,
                text_input.split("-")
            )

            total = end - start + 1

            if total > 2000:

                await message.answer(
                    "❌ Maximum 2000 IDs Allowed"
                )

                return

            await message.answer(
                f"🔍 Scanning {total} IDs..."
            )

            found = 0

            for sid in range(start, end + 1):

                result = check_student(
                    str(sid),
                    eiin
                )

                if result["valid"]:

                    found += 1

                    mobile = result["mobile"]

                    if mobile and mobile.startswith("0"):

                        whatsapp_number = "88" + mobile

                    else:

                        whatsapp_number = mobile

                    buttons = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="WhatsApp",
                                    url=f"https://wa.me/{whatsapp_number}"
                                ),

                                InlineKeyboardButton(
                                    text="Telegram",
                                    url="https://t.me/yourusername"
                                )
                            ]
                        ]
                    )

                    text = f"""
✅ VALID STUDENT

🆔 ID: {result['student_id']}
👤 Name: {result['name']}

🙍‍♂️ Father: {result['father']}
🙍‍♀️ Mother: {result['mother']}

📞 Mobile: {result['mobile']}
🚻 Gender: {result['gender']}

🎓 Class: {result['class']}
📚 Group: {result['group']}
🏫 Institute: {result['institute']}
"""

                    await message.answer(
                        text,
                        reply_markup=buttons
                    )

            await message.answer(
                f"✅ Scan Completed\n\n"
                f"Found: {found}"
            )

        except:

            await message.answer(
                "❌ Invalid Range Format"
            )

    # ========================================
    # SINGLE SEARCH
    # ========================================

    else:

        result = check_student(
            text_input,
            eiin
        )

        if result["valid"]:

            mobile = result["mobile"]

            if mobile and mobile.startswith("0"):

                whatsapp_number = "88" + mobile

            else:

                whatsapp_number = mobile

            buttons = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="WhatsApp",
                            url=f"https://wa.me/{whatsapp_number}"
                        ),

                        InlineKeyboardButton(
                            text="Telegram",
                            url="https://t.me/yourusername"
                        )
                    ]
                ]
            )

            text = f"""
✅ VALID STUDENT

🆔 ID: {result['student_id']}
👤 Name: {result['name']}

🙍‍♂️ Father: {result['father']}
🙍‍♀️ Mother: {result['mother']}

📞 Mobile: {result['mobile']}
🚻 Gender: {result['gender']}

🎓 Class: {result['class']}
📚 Group: {result['group']}
🏫 Institute: {result['institute']}
"""

            await message.answer(
                text,
                reply_markup=buttons
            )

        else:

            await message.answer(
                "❌ Student Not Found"
            )

    # ========================================
    # KEEP SAME EIIN
    # ========================================

    await state.set_state(
        StudentState.waiting_for_student
    )

# ============================================
# MAIN
# ============================================

async def main():

    print("Bot Started")

    threading.Thread(
        target=run_web
    ).start()

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
