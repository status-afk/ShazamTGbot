import logging
import httpx
import os
import tempfile
import re
from aiogram import types
from aiogram.types import InputFile, MediaGroup, InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, bot, cache_db,user_db
from aiogram.utils.markdown import html_decoration as hd

# Konfiguratsiya
RAPIDAPI_KEY = "a89071279emsh52d6dfefe773534p1ef94ejsn4a8c42c2ddb2"
API_URL = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
API_HOST = "auto-download-all-in-one.p.rapidapi.com"
FILE_SIZE_LIMIT = 50 * 1024 * 1024  # 50MB limit
REQUEST_TIMEOUT = 15.0  # so'rov vaqti
ADMINS = ["7376396301"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL REGEXP
HTTP_URL_REGEXP = r'^(https?://[^\s]+)$'

# Platformalarni aniqlash uchun minimal ro'yxat
PLATFORM_KEYWORDS = {
    "instagram.com": "Instagram",
    "youtu.be": "YouTube",
    "youtube.com": "YouTube",
    "facebook.com": "Facebook",
    "tiktok.com": "TikTok"
}

def get_platform_from_url(url: str) -> str:
    lower_url = url.lower()
    for keyword, platform_name in PLATFORM_KEYWORDS.items():
        if keyword in lower_url:
            return platform_name
    return "Unknown"

@dp.message_handler(regexp=HTTP_URL_REGEXP)
async def handle_media_request(message: types.Message):
    """
    Foydalanuvchi URL yuborganda media yuklab beruvchi handler.
    Avval DB dan cache ni tekshiradi, bo'lmasa API orqali yuklab, keyin DB ga saqlaydi.
    """
    user_db.activate_user(message.from_user.id)
    user_id = message.from_user.id
    url = message.text.strip()
    platform = get_platform_from_url(url)

    logger.info(f"User: {user_id}, URL: {url}, Platform: {platform}")
    downloading_message = await message.reply_sticker(
        "CAACAgEAAxkBAAMWZ0Hqfhu6E-BQLDjgWC2B0Dg_QpsAAoACAAKhYxlEq1g_ogXCTdw2BA"
    )

    # Statistika uchun increment
    cache_db.increment_request_count(platform)

    # Avval cache ni tekshiramiz
    cached_file_id = cache_db.get_file_id_by_url(url)
    if cached_file_id:
        # Cache da fayl bor, lekin media turi aniqlanmagan.
        # Shunchaki document sifatida yuboramiz.
        await send_cached_media(message, cached_file_id)
        await downloading_message.delete()
        return

        # Cache mavjud bo'lmasa API dan so'rov
        response_json = await fetch_media_info(url)
        if not response_json:
            await downloading_message.delete()
            await message.answer("⛔ Media topilmadi yoki yuklab olishda xatolik yuz berdi.")
            return

        medias = response_json.get('medias', [])
        if not medias:
            await downloading_message.delete()
            await message.answer("⛔ Ushbu URL dan yuklab bo'ladigan media topilmadi.")
            return

        try:
            await handle_all_platforms(message, url, platform, medias)
        except Exception as e:
            logger.error(f"Error handling media: {e}")
            await message.answer("⚠ Xatolik yuz berdi. Qayta urinib ko'ring.")
        finally:
            await downloading_message.delete()

async def fetch_media_info(url: str) -> dict:
    """
    API ga so'rov yuboradi va javobni dict ko'rinishda qaytaradi.
    Xatolik yuz bersa bo'sh dict qaytaradi.
    """
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    payload = {"url": url}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API returned non-200 status: {response.status_code}")
                return {}
    except httpx.TimeoutException:
        logger.error("Request timed out")
        return {}
    except Exception as e:
        logger.error(f"Error fetching media info: {e}")
        return {}

async def handle_all_platforms(message: types.Message, url: str, platform: str, medias: list):
    """
    Barcha platformalar uchun umumiy oqim:
    - Avval video qidiradi. Video bo'lsa, hajmini tekshiradi.
    - Video yo'q bo'lsa, image yoki audio ga o'tadi.
    - Katta fayl (>50MB) bo'lsa, link yuboradi.
    - Audio bo'lsa, inline button bilan yuborish imkoniyati.
    """
    video_medias = [m for m in medias if m.get('type') == 'video']
    image_medias = [m for m in medias if m.get('type') == 'image']
    audio_medias = [m for m in medias if m.get('type') == 'audio']

    caption = f"Obuna talab qilmaydigan yagona tezkor bot – @VkmShazamUzb_bot | TEZKOR YUKLASH"

    # Video bor-yo'qligini tekshirish
    if video_medias:
        chosen_video = video_medias[0]
        await process_and_send_media(message, chosen_video, platform, url, caption, audio_medias)
        return

    # Video yo'q, rasm yoki audio?
    if len(image_medias) > 1:
        # Bir nechta rasm
        await send_images_group(message, image_medias, platform, url, caption)
        return
    elif len(image_medias) == 1:
        # Bitta rasm
        await send_single_media(message, image_medias[0], platform, url, caption)
        return
    elif audio_medias:
        # Faqat audio
        await send_single_media(message, audio_medias[0], platform, url, caption)
        return
    else:
        # Hech narsa yo'q
        await message.answer("⛔ Ushbu URL da yuklab bo'ladigan media topilmadi.")


async def process_and_send_media(message: types.Message, media: dict, platform: str, url: str, caption: str, audio_medias: list):
    """
    Videoni yuklab yuborish, hajmini tekshirish.
    Agar audio ham bo'lsa, videodan keyin darhol audioni ham yuboradi.
    """
    media_url = media.get('url')
    file_path = await download_media('video', media_url)
    if not file_path:
        await message.answer("❌ Videoni yuklab bo'lmadi.")
        return

    file_size = os.path.getsize(file_path)
    if file_size > FILE_SIZE_LIMIT:
        # Fayl juda katta, link yuborish
        os.unlink(file_path)
        await message.answer(f"📎 Video hajmi juda katta (>50MB)\n{media_url}")
        return

    input_file = InputFile(file_path)
    sent_msg = await message.answer_video(input_file, caption=caption, parse_mode="HTML")

    if sent_msg.video:
        cache_db.add_cache(platform, url, sent_msg.video.file_id)
    os.unlink(file_path)

    # Agar audio mavjud bo'lsa, videodan so'ng uni ham yuboramiz
    if audio_medias:
        # Bitta audio ni olamiz (birinchisi)
        audio = audio_medias[0]
        a_url = audio.get('url')
        a_file_path = await download_media('audio', a_url)
        if not a_file_path:
            await message.answer("❌ Audioni yuklab bo'lmadi.")
            return

        a_sent_msg = await message.answer_audio(InputFile(a_file_path), caption=caption, parse_mode="HTML")
        if a_sent_msg.audio:
            cache_db.add_cache(platform, url, a_sent_msg.audio.file_id)
        os.unlink(a_file_path)

async def send_images_group(message: types.Message, image_medias: list, platform: str, url: str, caption: str):
    """
    Bir nechta rasmni MediaGroup sifatida yuborish, so'ng DB ga cacheni yozish.
    """
    media_group = MediaGroup()
    downloaded_files = []

    first = True
    for img in image_medias:
        img_url = img.get('url')
        file_path = await download_media('image', img_url)
        if not file_path:
            continue
        if first:
            media_group.attach_photo(InputFile(file_path), caption=caption, parse_mode="HTML")
            first = False
        else:
            media_group.attach_photo(InputFile(file_path))
        downloaded_files.append((file_path, 'image'))

    if downloaded_files:
        sent_messages = await message.answer_media_group(media_group)
        for msg, (fpath, m_type) in zip(sent_messages, downloaded_files):
            if msg.photo:
                cache_db.add_cache(platform, url, msg.photo[-1].file_id)
            os.unlink(fpath)

async def send_single_media(message: types.Message, media: dict, platform: str, url: str, caption: str):
    """
    Bitta media ni yuborish.
    Videoda hajmni tekshiradi, rasm va audio da to'g'ridan-to'g'ri yuboradi.
    """
    m_type = media.get('type')
    m_url = media.get('url')

    file_path = await download_media(m_type, m_url)
    if not file_path:
        await message.answer("❌ Mediani yuklab bo'lmadi.")
        return

    file_size = os.path.getsize(file_path)

    if m_type == 'video':
        if file_size > FILE_SIZE_LIMIT:
            os.unlink(file_path)
            await message.answer(f"📎 Video hajmi juda katta (>50MB)\n{m_url}")
            return
        sent_msg = await message.answer_video(InputFile(file_path), caption=caption, parse_mode="HTML")
        if sent_msg.video:
            cache_db.add_cache(platform, url, sent_msg.video.file_id)
    elif m_type == 'audio':
        sent_msg = await message.answer_audio(InputFile(file_path), caption=caption, parse_mode="HTML")
        if sent_msg.audio:
            cache_db.add_cache(platform, url, sent_msg.audio.file_id)
    elif m_type == 'image':
        sent_msg = await message.answer_photo(InputFile(file_path), caption=caption, parse_mode="HTML")
        if sent_msg.photo:
            cache_db.add_cache(platform, url, sent_msg.photo[-1].file_id)
    else:
        await message.answer("❔ Bu turdagi media qo'llab-quvvatlanmaydi.")
    os.unlink(file_path)

async def download_media(media_type: str, media_url: str) -> str:
    """
    Media yuklab olish uchun funksiya.
    """
    extension = ".mp4" if media_type == "video" else (".jpg" if media_type == "image" else ".mp3")

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(media_url)
            if resp.status_code == 200:
                with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp_file:
                    tmp_file.write(resp.content)
                    return tmp_file.name
            else:
                logger.warning(f"Failed to download media, status code: {resp.status_code}")
                return ""
    except httpx.TimeoutException:
        logger.error("Timeout while downloading media")
        return ""
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return ""


async def send_cached_media(message: types.Message, file_id: str):
    """
    Cache dan olingan media ni Telegram file_id orqali qayta yuborish.
    Media turi nomalum, shuning uchun universal yechim sifatida document sifatida yuboramiz.
    """
    caption = f"Obuna talab qilmaydigan yagona tezkor bot – @VkmShazamUzb_bot | TEZKOR YUKLASH"
    await message.answer_document(file_id, caption=caption, parse_mode="HTML")









