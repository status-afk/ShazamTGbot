from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db_api.users import UserDatabase
from utils.db_api.groups import GroupDatabase
from utils.db_api.channels import ChannelDatabase
from utils.db_api.cache import MediaCacheDatabase

from data import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
#database obyektlarini  yaratamiz
user_db=UserDatabase(path_to_db="data/user.db")
group_db=GroupDatabase(path_to_db="data/group.db")
channel_db=ChannelDatabase(path_to_db="data/channel.db")
cache_db=MediaCacheDatabase(path_to_db="data/cache.db")
