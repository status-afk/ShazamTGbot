from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging

from data.config import ADMINS
from loader import dp, channel_db, bot, user_db
from keyboards.default.default_keyboard import menu_admin, menu_ichki_kanal


# Kanallarni boshqarish uchun state-lar
class ChannelStates(StatesGroup):
    AddChannelInviteLink = State()
    AddChannelForwardMessage = State()
    RemoveChannel = State()


async def check_super_admin_permission(telegram_id: int):
    logging.info(f"Checking super admin permission for telegram_id: {telegram_id}")
    return telegram_id in ADMINS


async def check_admin_permission(telegram_id: int):
    logging.info(f"Checking admin permission for telegram_id: {telegram_id}")
    user = user_db.select_user(telegram_id=telegram_id)
    if not user:
        logging.info(f"No user found with telegram_id {telegram_id}")
        return False
    user_id = user[0]  # Users jadvalidagi id (user_id)
    admin = user_db.check_if_admin(user_id=user_id)
    logging.info(f"Admin check result for user_id {user_id}: {admin}")
    return admin


# Ortga qaytish handler
@dp.message_handler(Text("🔙 Ortga qaytish"))
async def back_handler(message: types.Message):
    telegram_id = message.from_user.id
    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        await message.answer("Siz bosh sahifadasiz", reply_markup=menu_admin)

# Kanallar boshqaruvi menyusi
@dp.message_handler(Text(equals="📢 Kanallar boshqaruvi"))
async def channel_management(message: types.Message):
    telegram_id = message.from_user.id
    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        await message.answer("Kanallar boshqaruvi", reply_markup=menu_ichki_kanal)


# Kanal qo'shish (state boshlanadi)
@dp.message_handler(Text(equals="➕ Kanal qo'shish"))
async def add_channel(message: types.Message):
    telegram_id = message.from_user.id
    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        await message.answer("Yangi kanalning taklif (invite) linkini kiriting yoki.")
        await ChannelStates.AddChannelInviteLink.set()


# Kanal qo'shish (invite linkni qabul qilish)
@dp.message_handler(state=ChannelStates.AddChannelInviteLink)
async def process_channel_invite_link(message: types.Message, state: FSMContext):
    invite_link = message.text.strip()
    await state.update_data(invite_link=invite_link)
    await message.answer("Endi kanalning istalgan xabarini oldinga yuboring (forward).")
    await ChannelStates.AddChannelForwardMessage.set()

# Kanal qo'shish (forward qilingan xabarni qabul qilish)
@dp.message_handler(state=ChannelStates.AddChannelForwardMessage, content_types=types.ContentTypes.ANY)
async def process_channel_forward_message(message: types.Message, state: FSMContext):
    if not message.forward_from_chat:
        await message.answer("Iltimos, kanalning xabarini oldinga yuboring (forward).")
        return

    channel_id = message.forward_from_chat.id
    title = message.forward_from_chat.title
    data = await state.get_data()
    invite_link = data.get('invite_link')

    try:
        # Botning kanalga administrator ekanligini tekshirish
        bot_member = await bot.get_chat_member(chat_id=channel_id, user_id=(await bot.me).id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer("❌ Bot ushbu kanalga administrator sifatida qo'shilmagan. Iltimos, botni kanalga administrator sifatida qo'shing.")
            await state.finish()
            return

        # Bazaga kanalni qo'shish
        channel_db.add_channel(channel_id=channel_id, title=title, invite_link=invite_link)
        logging.info(f"Channel added: ID {channel_id}, Title {title}, Invite Link {invite_link}")
        await message.answer(f"✅ {title} kanali muvaffaqiyatli qo'shildi!")

    except Exception as e:
        logging.error(f"Error adding channel: {e}")
        await message.answer("❌ Kanalni qo'shishda xatolik yuz berdi. Iltimos, to'g'ri ma'lumotlarni kiriting va botni kanalda administrator sifatida qo'shing.")

    await state.finish()

# Kanalni o'chirish (state boshlanadi)
@dp.message_handler(Text(equals="❌ Kanalni o'chirish"))
async def remove_channel(message: types.Message):
    telegram_id = message.from_user.id
    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        await message.answer("O‘chirilishi kerak bo‘lgan kanalning invite linkini kiriting.")
        await ChannelStates.RemoveChannel.set()


# Kanalni o'chirish (ID yoki invite linkni qabul qilish va o'chirish)
@dp.message_handler(state=ChannelStates.RemoveChannel)
async def process_channel_remove(message: types.Message, state: FSMContext):
    channel_identifier = message.text
    logging.info(f"Removing channel with identifier: {channel_identifier}")

    try:
        if channel_identifier.isdigit():
            channel_id = int(channel_identifier)
            channel_db.remove_channel(channel_id=channel_id)
            logging.info(f"Channel removed: ID {channel_id}")
            await message.answer(f"✅ Kanal ID {channel_id} muvaffaqiyatli o'chirildi!")
        else:
            channel_data = channel_db.get_channel_by_invite_link(channel_identifier)
            if channel_data:
                channel_id = channel_data[1]  # channel_id ni indeks orqali olish
                channel_db.remove_channel(channel_id=channel_id)
                logging.info(f"Channel removed: ID {channel_id}")
                await message.answer(f"✅ Kanal {channel_data[2]} muvaffaqiyatli o'chirildi!")  # title ni indeks orqali olish
            else:
                await message.answer("❌ Bunday kanal topilmadi.")
    except Exception as e:
        logging.error(f"Error removing channel: {e}")
        await message.answer("❌ Kanalni o'chirishda xatolik yuz berdi.")

    await state.finish()

# Barcha kanallar ro'yxatini ko'rsatish
@dp.message_handler(Text(equals="📋 Barcha kanallar"))
async def list_all_channels(message: types.Message):
    telegram_id = message.from_user.id
    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        channels = channel_db.get_all_channels()
        if not channels:
            await message.answer("❌ Hozircha tizimda hech qanday kanal mavjud emas.")
            return

        channel_list = []
        for channel in channels:
            channel_list.append(f"ID: {channel[1]} | Nomi: {channel[2]} | Invite Link: {channel[3]}")

        full_channel_list = "\n".join(channel_list)
        await message.answer(f"📋 Kanallar ro'yxati:\n\n{full_channel_list}")



