"""
crawler_to_firebase_with_utils.py (Playwright 版本)
從 Firebase「conditions」讀取條件 → 拼 591 URL → 爬 title/link → 寫入 notifications → 發送 email
"""

import time, sys, os, re, smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import firebase_admin
from firebase_admin import credentials, firestore

# === 載入 .env 檔案 ===
load_dotenv()

# === 區域代碼對照表（台北市 region=1）===
DISTRICT_SECTION = {
    "中正區": 1, "大同區": 2, "中山區": 3, "松山區": 4,
    "大安區": 5, "萬華區": 6, "信義區": 7, "士林區": 8,
    "北投區": 9, "內湖區": 10, "南港區": 11, "文山區": 12
}

# === 初始化 Firebase ===
cred_dict = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
}
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# === 建立查詢 URL ===
def build_url(cond: dict) -> str:
    url = "https://rent.591.com.tw/list?region=1"
    section = DISTRICT_SECTION.get(cond["district"])
    if section:
        url += f"&section={section}"
    url += f"&price={cond['minPrice']}${cond['maxPrice']}$"
    url += f"&acreage={cond['minSize']}${cond['maxSize']}$"
    if cond.get("allowPets"):
        url += "&other=pet"
    return url

# === 使用 Playwright 抓網頁 ===
def get_page_content(url: str) -> BeautifulSoup:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        ))
        page.goto(url, timeout=60000)

        try:
            page.wait_for_selector(".list-wrapper .item", timeout=10000)
        except:
            print("⚠️ 找不到房源列表元素，可能被擋或沒資料")

        content = page.content()
        browser.close()
    return BeautifulSoup(content, "html.parser")

# === 解析房源 ===
def parse_items(soup):
    results = []
    for item in soup.select(".list-wrapper .item"):
        title_tag = item.select_one("a.link")
        if not title_tag:
            continue

        title = title_tag.text.strip()
        link = title_tag["href"]

        updated = ""
        for line in item.select("span.line"):
            text = line.get_text(strip=True)
            if "更新" in text:
                updated = text
                break

        if "分鐘內更新" in updated:
            is_recent = True
        else:
            match = re.search(r"(\d+)小時內更新", updated)
            is_recent = match and int(match.group(1)) <= 3

        if is_recent:
            results.append({"title": title, "link": link, "updated": updated})
    return results

# === 寫入通知 ===
def write_notifications(user_id, condition_id, listings):
    for l in listings:
        db.collection("notifications").add({
            "userId": user_id,
            "conditionId": condition_id,
            "title": l["title"],
            "link": l["link"],
            "updated": l["updated"],
            "createdAt": firestore.SERVER_TIMESTAMP
        })

# === 查詢 email ===
def get_user_email(user_id):
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict().get("email")
    except Exception as e:
        print(f"⚠️ 無法查詢 email：{e}")
    return None

# === 發送 email ===
def send_email(to_email, count):
    from_email = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    subject = "開 Home 爬：有新的房屋通知囉！"
    body = f"您好，系統剛為您找到了 {count} 間符合條件的房屋資訊，請至您的通知頁面查看。"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"開 Home 爬 通知 <{from_email}>"
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, app_password)
            server.send_message(msg)
        print(f"📧 已寄信通知 {to_email}")
    except Exception as e:
        print(f"⚠️ 寄信失敗: {e}")

# === 主流程 ===
def main():
    cond_docs = db.collection("conditions").stream()

    for doc in cond_docs:
        cond = doc.to_dict()
        user_id = cond.get("userId")
        if not user_id:
            print("⚠️ 此條件缺少 userId，略過")
            continue

        if cond.get("city") != "台北市":
            continue

        url = build_url(cond)
        print(f"🔍 查詢條件網址: {url}")
        soup = get_page_content(url)
        listings = parse_items(soup)
        print(f"→ 符合條件房源數量：{len(listings)}")

        if listings:
            print(f"📥 寫入 {len(listings)} 條通知到 Firebase")
            write_notifications(user_id, doc.id, listings)

            email = get_user_email(user_id)
            if email:
                print(f"✅ 找到 email: {email}，準備寄信...")
                send_email(email, len(listings))
            else:
                print(f"❌ 找不到使用者 {user_id} 的 email")

    print("🎉 爬蟲完成，已寫入 Firebase 並寄送通知")

if __name__ == "__main__":
    main()
