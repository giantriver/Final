from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from crawler_591 import main as run_crawler
import uvicorn

app = FastAPI()

# ✅ 加入 CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定 http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run")
def trigger_crawler():
    run_crawler()
    return {"status": "success", "message": "已執行 crawler"}

if __name__ == "__main__":
    uvicorn.run("crawler_api:app", host="0.0.0.0", port=8000)
