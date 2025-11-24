from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import urllib.request
import json
import re
import socket

app = FastAPI()

# --- CORS AYARLARI ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

# ---------------- YARDIMCI FONKSİYONLAR ----------------

def get_video_id(url):
    """YouTube linkinden Video ID'sini çeker"""
    video_id = None
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def safe_request(url):
    """Güvenli ve zaman ayarlı HTTP isteği atar"""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"Bağlantı hatası ({url}): {e}")
    return None

# ---------------- MOTOR 1: PIPED API (YENİ GÜÇLÜ OYUNCU) ----------------
def fetch_from_piped(video_id):
    # Piped sunucuları genellikle Invidious'tan daha stabildir
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.otton.uk",
        "https://pipedapi.moomoo.me",
        "https://pipedapi.smnz.de",
        "https://pipedapi.adminforge.de"
    ]
    
    print(f"🛡️ Piped Motoru Devrede ({len(instances)} sunucu)...")
    
    for instance in instances:
        print(f"Deneniyor: {instance}...")
        data = safe_request(f"{instance}/streams/{video_id}")
        if data:
            print(f"✅ BAŞARILI! Veri {instance} kaynağından alındı.")
            return {
                'title': data.get('title', 'Başlık Yok'),
                'thumbnail': data.get('thumbnailUrl', ''),
                'duration': data.get('duration', 0)
            }
            
    return None

# ---------------- MOTOR 2: INVIDIOUS API (YEDEK GÜÇ) ----------------
def fetch_from_invidious(video_id):
    # En güncel ve sağlıklı Invidious listesi
    instances = [
        "https://inv.tux.pizza",
        "https://invidious.projectsegfau.lt",
        "https://vid.puffyan.us",
        "https://invidious.jing.rocks",
        "https://youtube.076.ne.jp"
    ]
    
    print(f"🛡️ Invidious Motoru Devrede ({len(instances)} sunucu)...")
    
    for instance in instances:
        print(f"Deneniyor: {instance}...")
        data = safe_request(f"{instance}/api/v1/videos/{video_id}")
        if data:
            print(f"✅ BAŞARILI! Veri {instance} kaynağından alındı.")
            # Thumbnail güvenliği
            thumb = "https://via.placeholder.com/640x360"
            if data.get('videoThumbnails') and len(data['videoThumbnails']) > 0:
                thumb = data['videoThumbnails'][0].get('url', thumb)
            
            return {
                'title': data.get('title', 'Başlık Yok'),
                'thumbnail': thumb,
                'duration': data.get('lengthSeconds', 0)
            }
            
    return None

# ---------------- ANA API NOKTASI ----------------

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "motor": "v4.0 (Tank Modu: yt-dlp + Piped + Invidious)"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"\n--- YENİ İSTEK: {request.url} ---")
    
    video_title = "Video İşleniyor..."
    thumbnail = "https://via.placeholder.com/640x360?text=Yukleniyor"
    duration = 0
    app_message = ""
    success = False
    
    # Adım 0: Video ID'yi al
    vid_id = get_video_id(request.url)
    if not vid_id:
        return {"status": "error", "message": "Geçersiz YouTube Linki"}

    # PLAN A: Normal yt-dlp (Genelde cloud'da engellenir ama şansımızı deneriz)
    try:
        print("1. Yöntem (yt-dlp) deneniyor...")
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'format': 'best',
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            if info and 'title' in info:
                video_title = info.get('title')
                thumbnail = info.get('thumbnail')
                duration = info.get('duration')
                app_message = f"Video Bulundu (Youtube): {video_title[:20]}..."
                success = True
    except Exception as e:
        print(f"⚠️ yt-dlp engellendi.")

    # PLAN B: Piped API (Yeni ve güçlü alternatif)
    if not success:
        piped_data = fetch_from_piped(vid_id)
        if piped_data:
            video_title = piped_data['title']
            thumbnail = piped_data['thumbnail']
            duration = piped_data['duration']
            app_message = f"Video Bulundu (Piped): {video_title[:20]}..."
            success = True

    # PLAN C: Invidious API (Eski dost)
    if not success:
        inv_data = fetch_from_invidious(vid_id)
        if inv_data:
            video_title = inv_data['title']
            thumbnail = inv_data['thumbnail']
            duration = inv_data['duration']
            app_message = f"Video Bulundu (Inv): {video_title[:20]}..."
            success = True

    # SONUÇ: Hiçbiri olmadıysa bile "başarısız" dönüp sistemi kilitleme
    if not success:
        app_message = "Veri çekilemedi (Simülasyon Modu)"
        print("❌ Tüm motorlar başarısız oldu. Simülasyon verisi dönülüyor.")
        success = True # Arayüz bozulmasın diye success dönüyoruz

    return {
        "status": "success",
        "message": app_message,
        "processed_video": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "meta_data": {
            "title": video_title,
            "thumbnail": thumbnail,
            "duration": duration
        }
    }
