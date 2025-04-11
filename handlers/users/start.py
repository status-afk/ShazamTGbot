from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from loader import dp, user_db

@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    # Foydalanuvchi bazada mavjudligini tekshirish
    user = user_db.select_user(telegram_id=telegram_id)
    if not user:
        # Yangi foydalanuvchini bazaga qo'shish
        user_db.create_table_users()
        user_db.add_user(telegram_id=telegram_id, username=username)
        welcome_text = (
            f"👋 Assalomu alaykum, {message.from_user.full_name}! \n\n"
            "<b>MUZOX</b> – siz uchun eng qulay va tezkor yuklab olish vositasi!🌟\n\n"
            "📸 <b>Instagram:</b> Postlar, Reels, Stories\n"
            "🎵 <b>TikTok:</b> Videolar va Musiqalar\n"
            "🎯 Havolani yuboring – yuklab oling! Tezkorlik uchun yagona tanlov\n\n"
            "<i>Obuna talab qilmaydigan yagona tezkor bot – @VkmShazamUzb_bot</i>"
        )

        await message.answer(welcome_text, parse_mode="HTML")
    else:
        # Foydalanuvchini qayta kelganligini yangilash va xush kelibsiz xabarini yuborish
        user_db.update_user_last_active(telegram_id=telegram_id)
        welcome_back_text = (
            f"👋 Yana salom, {message.from_user.full_name}! \n\n"
            "🎉 <b>MUZOX</b> bilan kontent yuklashni davom eting:\n"
            "📸 Instagram | 🎵 TikTok \n"
            "Havolani yuboring va tezkor yuklab oling! 😊"
        )
        await message.answer(welcome_back_text, parse_mode="HTML")
