from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.request
import json
import re

app = FastAPI()

# --- CORS İZİNLERİ ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

# ----------------- YARDIMCI ARAÇLAR -----------------

def get_video_id(url):
    """YouTube linkinden ID'yi çeker"""
    patterns = [r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None

def simple_request(url):
    """Basit HTTP isteği atar"""
    try:
        # İnsan gibi görünmek için User-Agent şart
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Hata ({url}): {e}")
        return None

# ----------------- MOTORLAR -----------------

def fetch_piped(video_id):
    """YÖNTEM 1: Piped API (En Temizi)"""
    servers = ["https://pipedapi.kavin.rocks", "https://api.piped.otton.uk", "https://pipedapi.moomoo.me"]
    print("1. Motor (Piped) deneniyor...")
    for server in servers:
        try:
            data = simple_request(f"{server}/streams/{video_id}")
            if data:
                j = json.loads(data)
                print(f"✅ Piped Başarılı: {server}")
                return {'title': j['title'], 'thumbnail': j['thumbnailUrl'], 'duration': 0}
        except: continue
    return None

def fetch_scraping(video_id):
    """YÖNTEM 2: HTML Scraping (NÜKLEER ÇÖZÜM)"""
    # API yok, Login yok. Doğrudan sayfayı okur.
    print("2. Motor (HTML Scraping) deneniyor...")
    url = f"https://www.youtube.com/watch?v={video_id}"
    html = simple_request(url)
    
    if html:
        try:
            # Sayfa kaynağından Başlığı bul
            title_match = re.search(r'<meta property="og:title" content="(.*?)">', html)
            title = title_match.group(1) if title_match else "YouTube Videosu"
            
            # Resmi bul
            img_match = re.search(r'<meta property="og:image" content="(.*?)">', html)
            thumbnail = img_match.group(1) if img_match else ""
            
            print("✅ Scraping Başarılı!")
            return {'title': title, 'thumbnail': thumbnail, 'duration': 0}
        except Exception as e:
            print(f"Scraping ayrıştırma hatası: {e}")
    
    return None

# ----------------- ANA PROGRAM -----------------

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "motor": "v5.0 (Nükleer Mod)"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"\nİstek: {request.url}")
    
    video_title = "Video İşleniyor..."
    thumbnail = "https://via.placeholder.com/640x360?text=Yukleniyor"
    success = False
    
    vid_id = get_video_id(request.url)
    if vid_id:
        # Önce Piped API dene
        data = fetch_piped(vid_id)
        
        # Olmazsa Nükleer Yöntemi (Scraping) dene
        if not data:
            data = fetch_scraping(vid_id)
            
        if data:
            video_title = data['title']
            thumbnail = data['thumbnail']
            success = True
            
    # Sonuç ne olursa olsun dön (Arayüz patlamasın)
    return {
        "status": "success",
        "message": f"Video Bulundu: {video_title[:20]}..." if success else "Veri Alınamadı (Manuel Giriş)",
        "processed_video": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "meta_data": {
            "title": video_title,
            "thumbnail": thumbnail,
            "duration": 0
        }
    }
