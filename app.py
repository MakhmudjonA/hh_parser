import os
import re
import json
import io
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd

from scraper import HHScraper

app = FastAPI(title="HH Vacancy Intelligence Dashboard", version="2.0.0")

# Ensure static directory exists
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global scraper instance and state
scraper = HHScraper()
latest_search_results: List[Dict[str, Any]] = []
search_state = {
    "is_searching": False,
    "progress": 0,
    "message": "Tayyor",
    "total_found": 0
}

class SearchRequest(BaseModel):
    query: str
    area: str = "2759"
    salary_from: Optional[int] = None
    experience: Optional[str] = None
    employment: Optional[str] = None
    schedule: Optional[str] = None
    pages: int = 1
    fetch_details: bool = False

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None
    session_cookies: Optional[str] = None

class CaptchaSolveRequest(BaseModel):
    captcha_text: str

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>HH Parser UI is loading... Please create static/index.html</h1>"

@app.get("/api/status")
async def get_status():
    return {
        "status": search_state,
        "is_authenticated": scraper.is_authenticated,
        "auth_user": scraper.auth_user,
        "results_count": len(latest_search_results)
    }

@app.post("/api/search")
async def start_search(req: SearchRequest):
    global latest_search_results, search_state
    
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Qidiruv so'zi kiritilishi shart!")

    search_state["is_searching"] = True
    search_state["progress"] = 10
    search_state["message"] = f"'{query}' bo'yicha qidiruv boshlanmoqda..."
    search_state["total_found"] = 0

    def progress_callback(info: Dict[str, Any]):
        search_state["message"] = info.get("message", "")
        if info.get("status") == "fetching_page":
            curr = info.get("current_page", 1)
            tot = info.get("total_pages", 1)
            search_state["progress"] = int((curr / max(tot, 1)) * 60)
        elif info.get("status") == "fetching_details":
            curr = info.get("current_item", 1)
            tot = info.get("total_items", 1)
            search_state["progress"] = 60 + int((curr / max(tot, 1)) * 38)
        elif info.get("status") == "completed":
            search_state["progress"] = 100

    try:
        results = scraper.search_vacancies(
            query=query,
            area=req.area,
            salary_from=req.salary_from,
            experience=req.experience if req.experience != "all" else None,
            employment=req.employment if req.employment != "all" else None,
            schedule=req.schedule if req.schedule != "all" else None,
            pages=min(max(req.pages, 1), 10),
            fetch_details=req.fetch_details,
            progress_callback=progress_callback
        )
        latest_search_results = results
        search_state["total_found"] = len(results)
        search_state["is_searching"] = False
        search_state["progress"] = 100
        search_state["message"] = f"Muvaffaqiyatli! {len(results)} ta vakansiya yuklandi."
        return {
            "success": True,
            "count": len(results),
            "vacancies": results
        }
    except Exception as e:
        search_state["is_searching"] = False
        search_state["message"] = f"Xatolik yuz berdi: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results")
async def get_results():
    return {
        "count": len(latest_search_results),
        "vacancies": latest_search_results
    }

@app.get("/api/stats")
async def get_stats():
    """Calculate aggregated stats from the latest search results."""
    if not latest_search_results:
        return {
            "total": 0,
            "with_salary": 0,
            "remote_count": 0,
            "avg_salary_usd": 0,
            "avg_salary_uzs": 0,
            "top_companies": [],
            "experience_distribution": {}
        }

    total = len(latest_search_results)
    with_salary = 0
    remote_count = 0
    usd_salaries = []
    uzs_salaries = []
    companies = {}
    exp_dist = {}

    for v in latest_search_results:
        # Salary
        sal_min = v.get("salary_min")
        sal_max = v.get("salary_max")
        cur = v.get("currency")
        if sal_min or sal_max:
            with_salary += 1
            avg_val = (sal_min + sal_max) / 2 if (sal_min and sal_max) else (sal_min or sal_max)
            if cur == "USD":
                usd_salaries.append(avg_val)
            elif cur == "UZS":
                uzs_salaries.append(avg_val)

        # Remote check
        is_remote = any("удал" in str(t).lower() or "remote" in str(t).lower() for t in v.get("tags", []))
        if is_remote or "удал" in str(v.get("address", "")).lower():
            remote_count += 1

        # Company
        comp = v.get("company", "Noma'lum")
        companies[comp] = companies.get(comp, 0) + 1

        # Experience
        exp = v.get("experience", "Boshqa")
        exp_dist[exp] = exp_dist.get(exp, 0) + 1

    top_comps = sorted([{"name": k, "count": v} for k, v in companies.items()], key=lambda x: x["count"], reverse=True)[:5]

    return {
        "total": total,
        "with_salary": with_salary,
        "remote_count": remote_count,
        "remote_percent": round((remote_count / total * 100), 1) if total > 0 else 0,
        "avg_salary_usd": int(sum(usd_salaries) / len(usd_salaries)) if usd_salaries else 0,
        "avg_salary_uzs": int(sum(uzs_salaries) / len(uzs_salaries)) if uzs_salaries else 0,
        "top_companies": top_comps,
        "experience_distribution": exp_dist
    }

@app.post("/api/auth/login")
async def login_user(req: LoginRequest):
    """
    Optional HH.uz credentials / session token injection.
    """
    if req.session_cookies:
        for item in req.session_cookies.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                scraper.session.cookies.set(k.strip(), v.strip(), domain=".hh.uz")
        scraper.is_authenticated = True
        scraper.auth_user = req.email or "Sessiya foydalanuvchisi"
        return {"success": True, "message": "Cookie sessiyasi muvaffaqiyatli saqlandi!"}

    if not req.email:
        raise HTTPException(status_code=400, detail="Email kiritilishi shart.")

    # Note: HeadHunter requires OTP codes for direct applicant login
    scraper.auth_user = req.email
    return {
        "success": True, 
        "requires_otp": True,
        "message": f"{req.email} uchun avtorizatsiya sozlamasi qabul qilindi. Vakansiyalarni qidirish loginsiz ham to'liq quvvatda ishlaydi!"
    }

@app.get("/api/export/csv")
async def export_csv():
    if not latest_search_results:
        raise HTTPException(status_code=400, detail="Eksport qilish uchun avval vakansiyalarni qidiring.")
    
    df = scraper.to_dataframe(latest_search_results)
    stream = io.StringIO()
    df.to_csv(stream, index=False, encoding='utf-8-sig')
    csv_bytes = stream.getvalue().encode('utf-8-sig')

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="hh_vakansiyalar.csv"'}
    )

@app.get("/api/export/excel")
async def export_excel():
    if not latest_search_results:
        raise HTTPException(status_code=400, detail="Eksport qilish uchun avval vakansiyalarni qidiring.")
    
    df = scraper.to_dataframe(latest_search_results)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Vakansiyalar')
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="hh_vakansiyalar.xlsx"'}
    )

@app.get("/api/export/json")
async def export_json():
    if not latest_search_results:
        raise HTTPException(status_code=400, detail="Eksport qilish uchun avval vakansiyalarni qidiring.")
    
    json_bytes = json.dumps(latest_search_results, ensure_ascii=False, indent=2).encode('utf-8')
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="hh_vakansiyalar.json"'}
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 HH Vacancy Intelligence Server ishga tushmoqda...")
    print("🌐 Brauzeringizda oching: http://localhost:8000")
    print("="*60 + "\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
