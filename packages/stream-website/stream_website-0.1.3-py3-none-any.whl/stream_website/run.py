import os
import subprocess
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    # İşletim sistemini tespit et
    system = platform.system().lower() 
    
    if system == "windows":
        executable_name = "mediamtx.exe"
    elif system == "linux":
        executable_name = "mediamtx_linux"
    elif system == "darwin": # macOS
        executable_name = "mediamtx_darwin"
    else:
        print(f"Hata: {system} işletim sistemi desteklenmiyor.")
        return

    mediamtx_path = BASE_DIR / "MediaMTX" / executable_name
    mediamtx_config = BASE_DIR / "MediaMTX" / "mediamtx.yml"

    # Linux ve Mac'te dosyaya çalıştırma izni (chmod +x) vermemiz gerekebilir
    if system != "windows":
        try:
            os.chmod(mediamtx_path, 0o755)
        except Exception as e:
            print(f"İzin hatası: {e}")

    if not mediamtx_path.exists():
        print(f"Hata: {executable_name} bulunamadı!")
        return

    print(f"{system.capitalize()} üzerinde MediaMTX başlatılıyor...")
    mediamtx_proc = subprocess.Popen([str(mediamtx_path), str(mediamtx_config)])
    print("Github Repository:https://github.com/AkbulutMirac/Stream-Website-Python-Module")

    try:
        import uvicorn
        uvicorn.run("stream_website.main:app", host="0.0.0.0", port=8000, reload=False)
    finally:
        mediamtx_proc.terminate()