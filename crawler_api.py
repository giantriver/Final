from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# 讀取 .env
load_dotenv()

# 初始化 app
app = FastAPI()

# CORS 設定（允許本地端前端連線）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 你也可以改成 ["http://localhost:5173"] 比較安全
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Railway API 資訊
RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN")
RAILWAY_PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID")
RAILWAY_SERVICE_ID = os.getenv("RAILWAY_SERVICE_ID")
print("🚀 RAILWAY_API_TOKEN:", bool(RAILWAY_API_TOKEN))
print("🚀 RAILWAY_PROJECT_ID:", RAILWAY_PROJECT_ID)
print("🚀 RAILWAY_SERVICE_ID:", RAILWAY_SERVICE_ID)

# 載入你的爬蟲主函式
from crawler_591 import main as run_crawler


@app.get("/")
def root():
    if not all([RAILWAY_API_TOKEN, RAILWAY_PROJECT_ID, RAILWAY_SERVICE_ID]):
        return {
            "status": "⚠️ 環境變數未正確載入",
            "RAILWAY_API_TOKEN": bool(RAILWAY_API_TOKEN),
            "RAILWAY_PROJECT_ID": bool(RAILWAY_PROJECT_ID),
            "RAILWAY_SERVICE_ID": bool(RAILWAY_SERVICE_ID),
        }

    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}"
    }
    test_url = f"https://backboard.railway.app/v2/projects/{RAILWAY_PROJECT_ID}/crons"
    try:
        response = requests.get(test_url, headers=headers)
        if response.status_code == 200:
            return {"status": "✅ Railway API 正常連線", "cron_count": len(response.json())}
        else:
            return {
                "status": "⚠️ 無法連線至 Railway API",
                "code": response.status_code,
                "error": response.text,
            }
    except Exception as e:
        return {
            "status": "❌ 發生例外錯誤",
            "error": str(e),
        }


@app.get("/run")
def run():
    try:
        run_crawler()
        return {"status": "爬蟲執行完成 ✅"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"執行錯誤：{e}")


class ScheduleRequest(BaseModel):
    interval_minutes: int


@app.post("/schedule")
def schedule(req: ScheduleRequest):
    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
        "Content-Type": "application/json"
    }

    cron_expr = f"*/{req.interval_minutes} * * * *"

    body = {
        "projectId": RAILWAY_PROJECT_ID,
        "serviceId": RAILWAY_SERVICE_ID,
        "name": "run-crawler-job",
        "schedule": cron_expr,
        "command": "python crawler_591.py"
    }

    response = requests.post("https://backboard.railway.app/v2/crons", json=body, headers=headers)

    # 🔽 加在這裡！列印錯誤訊息方便 debug
    print("🔧 Railway 回傳狀態碼:", response.status_code)
    print("📨 Railway 回傳內容:", response.text)

    if response.status_code == 200:
        return {"status": f"✅ 成功建立 CRON 任務，每 {req.interval_minutes} 分鐘執行一次"}
    else:
        raise HTTPException(status_code=500, detail=f"建立失敗: {response.text}")


@app.post("/cancel-schedule")
def cancel_schedule():
    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}"
    }

    list_url = f"https://backboard.railway.app/v2/projects/{RAILWAY_PROJECT_ID}/crons"
    resp = requests.get(list_url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="❌ 讀取 CRON 清單失敗")

    cron_list = resp.json()
    deleted = 0

    for cron in cron_list:
        if cron["name"] == "run-crawler-job":
            delete_url = f"https://backboard.railway.app/v2/crons/{cron['id']}"
            del_resp = requests.delete(delete_url, headers=headers)
            if del_resp.status_code == 200:
                deleted += 1

    return {"deleted": deleted, "message": f"🧹 已刪除 {deleted} 個 CRON 任務"}
