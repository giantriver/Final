from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

# 讀取 .env
load_dotenv()

app = FastAPI()

# Railway API 基本資訊
RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN")
RAILWAY_PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID")
RAILWAY_SERVICE_ID = os.getenv("RAILWAY_SERVICE_ID")

# 載入你的爬蟲主函式
from crawler_591 import main as run_crawler


@app.get("/")
def root():
    return {"message": "Crawler API Running ✅"}


@app.get("/run")
def run():
    try:
        run_crawler()
        return {"status": "爬蟲執行完成 ✅"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"執行錯誤：{e}")


# 前端傳來的資料格式
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
    if response.status_code == 200:
        return {"status": "成功建立 CRON 任務 ✅"}
    else:
        raise HTTPException(status_code=500, detail=f"建立失敗: {response.text}")


@app.post("/cancel-schedule")
def cancel_schedule():
    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}"
    }

    # 查找所有 CRON 任務
    list_url = f"https://backboard.railway.app/v2/projects/{RAILWAY_PROJECT_ID}/crons"
    resp = requests.get(list_url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="讀取 CRON 清單失敗")

    cron_list = resp.json()
    deleted = 0

    for cron in cron_list:
        if cron["name"] == "run-crawler-job":
            delete_url = f"https://backboard.railway.app/v2/crons/{cron['id']}"
            del_resp = requests.delete(delete_url, headers=headers)
            if del_resp.status_code == 200:
                deleted += 1

    return {"deleted": deleted, "message": f"已刪除 {deleted} 個 CRON 任務 ✅"}
