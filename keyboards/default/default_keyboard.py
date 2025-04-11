from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Asosiy admin menyusi uchun tugmalar
menu_admin = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📊 Statistika'),
            KeyboardButton(text='📣 Reklama'),
        ],
        [
            KeyboardButton(text='📢 Kanallar boshqaruvi'),
            KeyboardButton(text='👥 Adminlar boshqaruvi'),
        ],
        [
            KeyboardButton(text='📄 Yordam'),
            KeyboardButton(text='🔙 Ortga qaytish'),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Admin boshqaruvi menyusi uchun tugmalar
menu_ichki_admin = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='➕ Admin qo\'shish'),
            KeyboardButton(text='❌ Adminni o\'chirish'),
        ],
        [
            KeyboardButton(text='👥 Barcha adminlar'),
            KeyboardButton(text='🔙 Ortga qaytish'),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Kanal boshqaruvi menyusi uchun tugmalar
menu_ichki_kanal = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='➕ Kanal qo\'shish'),
            KeyboardButton(text='❌ Kanalni o\'chirish'),
        ],
        [
            KeyboardButton(text='📋 Barcha kanallar'),
            KeyboardButton(text='🔙 Ortga qaytish'),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Admin paneldan foydalanish uchun qo'shimcha tugmalar
def admin_btn():
    btn = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
    statistika = KeyboardButton("📊 Statistika")
    reklama = KeyboardButton("🎁 Reklama")
    add_channel = KeyboardButton("🖇 Kanallar boshqaruvi")
    return btn.add(statistika, reklama, add_channel)



# Kanallar uchun boshqaruv menyusi
def channels_btn():
    btn = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    add_channel = KeyboardButton("⚙ Kanal qo'shish")
    delete_channel = KeyboardButton("🗑 Kanalni o'chirish")
    exits = KeyboardButton("🔙 Ortga qaytish")
    return btn.add(add_channel, delete_channel, exits)

# Ortga qaytish uchun tugma
def exit_btn():
    btn = ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)
    return btn.add("🔙 Ortga qaytish")
