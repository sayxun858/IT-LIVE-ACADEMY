import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylni tekshiring.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. Tugmalar yaratamiz
button1 = KeyboardButton(text="📚 Kurslar")
button2 = KeyboardButton(text="🕒 Dars jadvali")
button3 = KeyboardButton(text="👨‍💻 IT haqida")
button4 = KeyboardButton(text="📞 Aloqa")

# 2. Tugmalarni klaviaturaga joylashtiramiz
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [button1, button2],
        [button3, button4]
    ],
    resize_keyboard=True
)

# 3. Start komandasi
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Assalomu alaykum! IT LIVE botiga xush kelibsiz! 🚀\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=keyboard
    )

# 4. Help komandasi
@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Botdan foydalanish uchun quyidagi tugmalardan foydalaning.",
         reply_markup=keyboard
    )

# 5. Kurslar tugmasi
@dp.message(F.text == "📚 Kurslar")
async def courses(message: Message):
    await message.answer(
        "Bizning kurslarimiz:\n"
        "1. Python\n"
        "2. C++\n"
        "3. Frontend"
    )

# 6. Dars jadvali tugmasi
@dp.message(F.text == "🕒 Dars jadvali")
async def schedule(message: Message):
    await message.answer(
        "Darslarimiz haftaning dushanba-shanba kunlari o'tiladi."
    )

# 7. IT haqida tugmasi
@dp.message(F.text == "👨‍💻 IT haqida")
async def about_it(message: Message):
    await message.answer(
        "IT — axborot texnologiyalari sohasi. "
        "Bu sohada dasturlash, dizayn va boshqa yo'nalishlar mavjud."
    )

# 8. Aloqa tugmasi
@dp.message(F.text == "📞 Aloqa")
async def contact(message: Message):
    await message.answer(
        "Biz bilan bog'lanish uchun administratorga murojaat qiling. \n"
        "Tel: 88 713 06 36"
    )

# 9. Noma'lum xabarlar
@dp.message()
async def unknown(message: Message):
    await message.answer(
        "Kechirasiz, bu xabarni tushunmadim. "
        "Menyudagi tugmalardan foydalaning."
    )

# 10. Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
