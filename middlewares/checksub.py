import logging
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from loader import dp
from utils.misc import subscription
from loader import bot, channel_db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class SubscriptionMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        if update.message:
            user = update.message.from_user.id
            if update.message.text in ['/start', '/help']:
                return
        elif update.callback_query:
            user = update.callback_query.from_user.id
            if update.callback_query.data == "check_subs":
                return
        else:
            return

        result = "⚠ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n"
        final_status = True

        # Bazadan barcha kanallarni olish
        channels = channel_db.get_all_channels()
        for channel in channels:
            channel_id = channel[1]  # channel_id ni olish
            title = channel[2]  # title ni olish
            invite_link = channel[3]  # invite_link ni olish

            # Foydalanuvchi kanalga obuna bo'lganligini tekshirish
            status = await subscription.check(user_id=user, channel=channel_id)

            final_status = final_status and status

            # Agar foydalanuvchi obuna bo'lmagan bo'lsa, invite_link orqali xabar qilish
            if not status:
                result += f"👉 <a href='{invite_link}'>{title}</a>\n"

        if not final_status:
            # "Obunani tekshirish" tugmasini yaratamiz
            check_button = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subs")]
                ]
            )
            if update.message:
                await update.message.answer(
                    result,
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                    reply_markup=check_button
                )
            elif update.callback_query:
                await update.callback_query.message.answer(
                    result,
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                    reply_markup=check_button
                )
            raise CancelHandler()
@dp.callback_query_handler(text="check_subs")
async def check_subscriptions(call: types.CallbackQuery):
    user = call.from_user.id
    result = "⚠ Hali ham quyidagi kanallarga obuna bo'lmagansiz:\n"
    final_status = True

    channels = channel_db.get_all_channels()

    for channel in channels:
        channel_id = channel[1]
        title = channel[2]
        invite_link = channel[3]

        status = await subscription.check(user_id=user, channel=channel_id)
        final_status = final_status and status

        if not status:
            result += f"👉 <a href='{invite_link}'>{title}</a>\n"

    if final_status:
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Siz barcha kanallarga obuna bo'lgansiz. Endi botdan foydalanishingiz mumkin.")
        # Agar kerak bo'lsa, foydalanuvchini asosiy menyuga yoki boshqa joyga yo'naltirishingiz mumkin
    else:
        await call.answer("❌ Siz hali ham barcha kanallarga obuna bo'lmadingiz.", show_alert=True)
        await call.message.edit_text(
            result,
            disable_web_page_preview=True,
            parse_mode="HTML",
            reply_markup=call.message.reply_markup
        )
