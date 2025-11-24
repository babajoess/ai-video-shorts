from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import urllib.request
import json
import re

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

def get_video_id(url):
    """YouTube linkinden Video ID'sini ayıklar"""
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

def fetch_from_invidious(video_id):
    """YouTube engellerse veriyi Invidious API'den çeker (Yedek Plan)"""
    # Halka açık, güvenilir Invidious sunucuları
    instances = [
        "https://inv.tux.pizza",
        "https://invidious.projectsegfau.lt",
        "https://vid.puffyan.us"
    ]
    
    for instance in instances:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            print(f"Yedek Sunucu Deneniyor: {instance}")
            
            # Python'un kendi kütüphanesiyle istek atıyoruz (Ekstra kütüphane gerekmez)
            req = urllib.request.Request(
                api_url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print("Yedek Sunucudan Veri Alındı!")
                    return {
                        'title': data.get('title'),
                        'thumbnail': data.get('videoThumbnails', [{}])[0].get('url'),
                        'duration': data.get('lengthSeconds')
                    }
        except Exception as e:
            print(f"Sunucu hatası ({instance}): {e}")
            continue
    return None

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "motor": "Hibrit (yt-dlp + Invidious)"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"İstek geldi: {request.url}")
    
    video_title = "Bilinmeyen Video"
    thumbnail = "https://via.placeholder.com/640x360?text=Video+Bulunamadi"
    duration = 0
    app_message = ""
    success = False

    # 1. YÖNTEM: Normal yt-dlp (Önce bunu dener)
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'nocheckcertificate': True,
            'ignoreerrors': True,
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
        print(f"yt-dlp Engellendi: {e}")

    # 2. YÖNTEM: Eğer yukarıdaki başarısız olursa "Arka Kapı"yı (Invidious) kullan
    if not success:
        print("yt-dlp başarısız oldu, B Planına geçiliyor...")
        vid_id = get_video_id(request.url)
        if vid_id:
            fallback_data = fetch_from_invidious(vid_id)
            if fallback_data:
                video_title = fallback_data['title']
                # Thumbnail bazen göreceli link gelir, düzeltelim
                thumb = fallback_data['thumbnail']
                if thumb and not thumb.startswith('http'):
                     thumbnail = f"https://inv.tux.pizza{thumb}"
                else:
                     thumbnail = thumb
                
                duration = fallback_data['duration']
                app_message = f"Video Bulundu (API): {video_title[:20]}..."
                success = True
            else:
                app_message = "Tüm sunucular meşgul, lütfen tekrar dene."
        else:
             app_message = "Geçersiz YouTube Linki"

    # Sonuç Dönüşü
    return {
        "status": "success" if success else "error",
        "message": app_message,
        "processed_video": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "meta_data": {
            "title": video_title,
            "thumbnail": thumbnail,
            "duration": duration
        }
    }
