import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("\n" + "="*65)
    print("🚀 HH Vacancy Intelligence Dashboard ishga tushmoqda...")
    print("🌐 Brauzer manzili: http://localhost:8000")
    print("🐳 Docker rejimida ishga tushirish uchun: docker run -p 8000:8000 hh-parser")
    print("="*65 + "\n")
    
    # Optionally open browser automatically in local dev
    try:
        threading.Thread(target=open_browser, daemon=True).start()
    except Exception:
        pass

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
