import os
import re
import json
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Init bot
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Constants
DOWNLOAD_FOLDER = "downloads"
USERS_FILE = "users.json"
ADMINS = ["7376396301"]  # Admin IDs

# State for broadcasting
class BroadcastState(StatesGroup):
    waiting_for_content = State()

# Ensure downloads folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Load/save users
user_search_results = {}
def load_users():
    """Load user data from file."""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Failed to load users: {e}")
        return {}

def save_users(users):
    """Save user data to file."""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    except Exception as e:
        logger.error(f"Failed to save users: {e}")

users = load_users()

def is_admin(user_id):
    return str(user_id) in ADMINS

# Admin commands
@dp.message_handler(commands=["stats"])
async def get_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ You are not an admin!")
    total_users = len(users)
    total_downloads = sum(u.get("downloads", 0) for u in users.values())
    await message.reply(f"📊 **Bot Statistics**\n\n👥 Total Users: {total_users}\n🎵 Total Downloads: {total_downloads}")

@dp.message_handler(commands=["broadcast"], state="*")
async def start_broadcast(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ You are not an admin!")
    await message.reply("📢 Send the message you want to broadcast (text, photo, or video).")
    await BroadcastState.waiting_for_content.set()

@dp.message_handler(state=BroadcastState.waiting_for_content, content_types=types.ContentTypes.ANY)
async def broadcast_content(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await state.finish()

    total_sent = 0
    for user_id in users.keys():
        try:
            if message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
            else:
                await bot.send_message(user_id, message.text or "📢 Announcement")
            total_sent += 1
        except Exception as e:
            logger.warning(f"Failed to broadcast to {user_id}: {e}")

    await message.reply(f"✅ Broadcast sent to {total_sent} users.")
    await state.finish()

# YouTube search helpers
def has_invalid_chars(title):
    """Check for invalid filename characters."""
    return bool(re.search(r'[\\/*?:"<>|]', title))

def parse_duration(seconds):
    """Filter durations up to 5 minutes."""
    return seconds is not None and seconds <= 300  # Max 5:00

def search_youtube(song_name):
    """Search YouTube for a song and return up to 10 filtered video results."""
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "cookies": "/app/cookies.txt",
    }

    logger.info(f"Searching YouTube for: {song_name}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch15:{song_name}"  # Request 15 to ensure 10 after filtering
            search_results = ydl.extract_info(search_query, download=False)
    except Exception as e:
        logger.error(f"Failed to search YouTube: {e}")
        return []

    logger.debug(f"Raw search results: {search_results}")
    if not search_results or "entries" not in search_results:
        logger.warning("No search results or entries found.")
        return []

    filtered_results = []
    skipped_count = 0
    for entry in search_results["entries"]:
        if len(filtered_results) >= 10:
            logger.info("Reached 10 results, stopping.")
            break

        logger.debug(f"Processing entry: {entry}")
        if not entry:
            logger.warning("Skipped: Empty entry")
            skipped_count += 1
            continue

        title = entry.get("title", "")
        duration = entry.get("duration")
        url = entry.get("webpage_url")  # YouTube video URL

        if not url:
            logger.warning(f"Skipped (no URL found): {title}")
            skipped_count += 1
            continue
        if has_invalid_chars(title):
            logger.warning(f"Skipped (invalid chars): {title}")
            skipped_count += 1
            continue
        if not parse_duration(duration):
            logger.warning(f"Skipped (bad duration): {title} ({duration}s)")
            skipped_count += 1
            continue

        logger.info(f"Accepted: {title} ({duration}s) - {url}")
        filtered_results.append({
            "title": title,
            "url": url
        })

    logger.info(f"Processed {len(search_results['entries'])} entries: {len(filtered_results)} accepted, {skipped_count} skipped")
    if len(filtered_results) < 10:
        logger.warning(f"Only {len(filtered_results)} results found after filtering (wanted 10)")
    return filtered_results

# Audio downloader
def download_audio(url):
    """Download audio from a YouTube URL."""
    if not url or not isinstance(url, str):
        logger.error(f"Invalid URL passed to downloader: {url}")
        return None

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading audio from: {url}")
            info = ydl.extract_info(url, download=True)
            if "title" in info:
                filename = f"{info['title']}.mp3"
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    logger.info(f"Download successful: {file_path}")
                    return file_path
                logger.error(f"File not found after download: {file_path}")
    except Exception as e:
        logger.error(f"Error during download: {e}")
    return None

# Bot commands
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"downloads": 0}
        save_users(users)
    await message.answer("🎶 Menga qo'shiq nomini yuboring, men uni topib beraman!")

@dp.message_handler()
async def find_song(message: types.Message):
    song_name = message.text.strip()
    await message.reply("🔎 Qo'shiq izlanmoqda...")
    results = search_youtube(song_name)
    if not results:
        return await message.reply("❌ Qo'shiq topilmadi. Boshqa nom kiriting.")

    user_search_results[message.from_user.id] = results
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(*[
        InlineKeyboardButton(text=str(i+1), callback_data=f"choose_{i}")
        for i in range(len(results))
    ])
    result_text = "\n".join([f"{i+1}. {r['title']}" for i, r in enumerate(results)])
    await message.reply(result_text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("choose_"))
async def choose_song(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id not in user_search_results:
        await bot.answer_callback_query(callback_query.id, text="❌ Siz hech qanday qo‘shiq izlamadingiz.")
        return

    try:
        song_index = int(callback_query.data.split("_")[1])
        if song_index < 0 or song_index >= len(user_search_results[user_id]):
            raise ValueError
    except (IndexError, ValueError):
        await bot.answer_callback_query(callback_query.id, text="❌ Noto‘g‘ri tanlov.")
        return

    selected_song = user_search_results[user_id][song_index]
    video_url = selected_song["url"]

    logger.debug(f"All search results for {user_id}: {user_search_results[user_id]}")
    logger.info(f"Selected song: {selected_song}")
    logger.info(f"Video URL: {video_url}")

    if not video_url:
        await bot.answer_callback_query(callback_query.id, text="❌ Invalid URL.")
        return

    await bot.send_message(user_id, f"🎶 **{selected_song['title']}** yuklanmoqda...\n⏳ Iltimos, kuting!")

    try:
        file_path = download_audio(video_url)
        if file_path:
            users[str(user_id)]["downloads"] += 1
            save_users(users)
            await bot.send_audio(user_id, audio=types.InputFile(file_path), title=selected_song["title"])
            os.remove(file_path)
        else:
            await bot.send_message(user_id, "❌ Qo‘shiq yuklab bo‘lmadi.")
    except Exception as e:
        logger.error(f"Error sending audio: {e}")
        await bot.send_message(user_id, "❌ Xatolik yuz berdi.")

    await bot.answer_callback_query(callback_query.id)

if __name__ == "__main__":
    logger.info("🤖 Bot ishga tushdi...")
    executor.start_polling(dp, skip_updates=True)