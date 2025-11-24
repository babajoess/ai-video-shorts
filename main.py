from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

# --- CORS AYARLARI (Wix'in bağlanması için) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "mesaj": "YouTube motoru hazır!"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"İstek geldi: {request.url}")
    
    # Varsayılan Değerler (Hata olursa dönecekler)
    video_title = "Örnek Video: Big Buck Bunny"
    thumbnail = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/800px-Big_buck_bunny_poster_big.jpg"
    duration = 60
    app_message = ""
    
    try:
        # 1. YouTube Ayarları (Çerez Destekli)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'nocheckcertificate': True,
            'ignoreerrors': True,
            
            # --- ÖNEMLİ: Çerez dosyasını buradan okuyor ---
            'cookiefile': 'cookies.txt', 
            # ----------------------------------------------
            
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=False dedik çünkü sadece başlığı çekiyoruz, videoyu indirmiyoruz
            info = ydl.extract_info(request.url, download=False)
            
            if info:
                video_title = info.get('title', video_title)
                thumbnail = info.get('thumbnail', thumbnail)
                duration = info.get('duration', duration)
                app_message = f"Video Bulundu: {video_title[:20]}..."
                print(f"BAŞARILI: {video_title}")
            
    except Exception as e:
        # YouTube engellerse veya cookies.txt yoksa burası çalışır
        print(f"HATA OLUŞTU: {str(e)}")
        app_message = "Video Bilgisi Alınamadı (Simülasyon)"

    # 2. Sonucu Wix'e gönder
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
