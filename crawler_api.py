# crawler_api.py
from fastapi import FastAPI
from crawler_591 import main as run_crawler
import uvicorn

app = FastAPI()

@app.post("/run")
def trigger_crawler():
    run_crawler()
    return {"status": "success", "message": "已執行 crawler"}

if __name__ == "__main__":
    uvicorn.run("crawler_api:app", host="0.0.0.0", port=8000)
