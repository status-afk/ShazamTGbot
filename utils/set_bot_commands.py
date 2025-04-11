from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Botni ishga tushurish"),
            types.BotCommand("top", "TOP  Popular Songs"),
            types.BotCommand("new", "NEW Popular  Songs"),
        ]
    )
