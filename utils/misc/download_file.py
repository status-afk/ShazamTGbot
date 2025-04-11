import httpx
from bs4 import BeautifulSoup
import os

# Umumiy funksiya request qilish uchun
def fetch_data(url):
    try:
        response = httpx.get(url, timeout=10.0, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Xato bo'lsa, exception chiqaradi
        return BeautifulSoup(response.text, 'html.parser')
    except httpx.HTTPStatusError as e:
        print(f"HTTP status error: {e}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")
    return None



def main_data():
    soup = fetch_data('https://xitmuzon.net/')
    if soup:
        data = soup.find_all('div', {'class': 'track-item fx-row fx-middle js-item js-share-item'})
        desk = []
        for i in data:
            desk.append({"artist": i['data-artist'], "title": i['data-title'], "track": i['data-track']})
        return desk
    return []

def new_trek():
    soup = fetch_data('https://uzhits.net/')
    if soup:
        data = soup.find_all('div', {'class': 'sect-col'})
        if data:
            top_data = data[0].find_all('div', {'class': 'track-item fx-row fx-middle js-item'})
            desk = []
            sana = 1
            for i in top_data:
                desk.append({"id": str(sana), "artist": i['data-artist'], "title": i['data-title'], "track": i['data-track']})
                sana += 1
            return desk
    return []


def top_music():
    soup = fetch_data('https://uzhits.net/')
    if soup:
        data = soup.find_all('div', {'class': 'sect-col'})
        if len(data) > 1:
            top_data = data[1].find_all('div', {'class': 'track-item fx-row fx-middle js-item'})
            desk = []
            sana = 11
            for i in top_data:
                desk.append({"id": str(sana), "artist": i['data-artist'], "title": i['data-title'], "track": i['data-track']})
                sana += 1
            return desk
    return []

def world_music():
    soup = fetch_data('https://xitmuzon.net/musics/tiktok')
    if soup:
        data = soup.find_all('div', {'class': 'track-item fx-row fx-middle js-item js-share-item'})
        desk = []
        sana = 21
        for i in data:
            desk.append({"id": str(sana), "track": i['data-track'], "artist": i['data-artist'], "title": i['data-title']})
            sana += 1
        return desk
    return []


# Qo'shiq yoki muallif bo'yicha qidirish funksiyasi
def search_music(search_query, music_list):
    results = []
    query_lower = search_query.lower()

    for track in music_list:
        artist_lower = track['artist'].lower()
        title_lower = track['title'].lower()

        if query_lower in artist_lower or query_lower in title_lower:
            results.append(track)

    return results

def search_example():
    # Musiqalar ro'yxatini yuklash
    all_music = main_data() + new_trek() + top_music() + world_music()

    # Foydalanuvchi qidirayotgan qo'shiq yoki muallif
    search_query = input("Qo'shiq yoki muallifni kiriting: ")

    # Qidiruv natijalari
    found_tracks = search_music(search_query, all_music)

    if found_tracks:
        for idx, track in enumerate(found_tracks, 1):
            print(f"{idx}. {track['artist']} - {track['title']}")
    else:
        print("Hech narsa topilmadi.")
