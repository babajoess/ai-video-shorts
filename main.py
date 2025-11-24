from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

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

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "mesaj": "YouTube motoru hazır!"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"İstek geldi: {request.url}")
    
    try:
        # 1. YouTube'dan video bilgilerini çek (İndirmeden)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_title = info.get('title', 'Başlık Bulunamadı')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            
        print(f"Video Bulundu: {video_title}")

        # 2. Sonucu Wix'e gönder
        return {
            "status": "success",
            "message": f"Video Bulundu: {video_title}",
            # Şimdilik videoyu işlemediğimiz için yine örnek video dönüyoruz ama
            # Mesaj kısmında GERÇEK video ismini göreceksin.
            "processed_video": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "meta_data": {
                "title": video_title,
                "thumbnail": thumbnail,
                "duration": duration
            }
        }

    except Exception as e:
        print(f"Hata: {str(e)}")
        return {
            "status": "error", 
            "message": f"YouTube Hatası: {str(e)}"
        }
