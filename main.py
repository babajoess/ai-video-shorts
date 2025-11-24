from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess

app = FastAPI()

# --- KRİTİK AYAR: CORS (Wix'in erişimine izin ver) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Gerçekte buraya sadece wix site adresin yazılır, şimdilik herkese açık
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"durum": "Sunucu Aktif", "mesaj": "Hazırım!"}

@app.post("/analyze")
def analyze_video(request: VideoRequest):
    print(f"Wix'ten gelen istek: {request.url}")

    # FFmpeg kontrolü (Sadece bilgi amaçlı)
    try:
        ffmpeg_version = subprocess.check_output(["ffmpeg", "-version"]).decode("utf-8").split("\n")[0]
    except:
        ffmpeg_version = "Bulunamadı"

    # --- SİMÜLASYON SONUCU ---
    # Gerçek işlem uzun süreceği için şimdilik hazır bir video dönüyoruz.
    return {
        "status": "success",
        "processed_video": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "message": f"Bağlantı Başarılı! Sunucu: {ffmpeg_version}"
    }
