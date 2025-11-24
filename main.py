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
    # GÜNCELLENMİŞ VE GENİŞLETİLMİŞ SUNUCU LİSTESİ
    instances = [
        "https://invidious.drgns.space",       # Almanya (Genelde hızlı)
        "https://invidious.fdn.fr",            # Fransa (Çok sağlam)
        "https://invidious.perennialteks.com", # ABD
        "https://yt.artemislena.eu",           # Avrupa
        "https://invidious.protokolla.fi",     # Finlandiya
        "https://iv.ggtyler.dev",              # ABD
        "https://inv.tux.pizza",               # Yedek
    ]
    
    print(f"B Planı Devrede: {len(instances)} adet sunucu denenecek...")

    for instance in instances:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            print(f"Deneniyor: {instance} ...")
            
            # Tarayıcı gibi davranarak istek at
            req = urllib.request.Request(
                api_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            # Timeout süresini 8 saniyeye çıkardık
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"BAŞARILI! Veri {instance} adresinden alındı.")
                    
                    # Thumbnail güvenliği (Bazen boş gelebilir)
                    thumb_url = "https://via.placeholder.com/640x360"
                    if data.get('videoThumbnails') and len(data['videoThumbnails']) > 0:
                        thumb_url = data['videoThumbnails'][0].get('url', thumb_url)
                    
                    return {
                        'title': data.get('title', 'Başlık Alınamadı'),
                        'thumbnail': thumb_url,
                        'duration': data.get('lengthSeconds', 0)
                    }
        except Exception as e:
            print(f"❌ {instance} başarısız: {e}")
            continue
            
    print("Tüm sunucular denendi ama yanıt alınamadı.")
    return None

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "motor": "v3.0 (Genişletilmiş Liste)"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"İstek geldi: {request.url}")
    
    video_title = "Video İşleniyor..."
    thumbnail = "https://via.placeholder.com/640x360?text=Yukleniyor"
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
        print(f"yt-dlp Engellendi, B Planına geçiliyor...")

    # 2. YÖNTEM: Eğer yukarıdaki başarısız olursa "Genişletilmiş B Planı"nı kullan
    if not success:
        vid_id = get_video_id(request.url)
        if vid_id:
            fallback_data = fetch_from_invidious(vid_id)
            if fallback_data:
                video_title = fallback_data['title']
                thumbnail = fallback_data['thumbnail']
                # Eğer thumbnail göreceli link ise (http ile başlamıyorsa) düzelt
                if thumbnail and not thumbnail.startswith('http'):
                     thumbnail = f"https://invidious.drgns.space{thumbnail}"
                
                duration = fallback_data['duration']
                app_message = f"Video Bulundu (Vekil): {video_title[:20]}..."
                success = True
            else:
                app_message = "Yoğunluk var, lütfen tekrar deneyin."
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
