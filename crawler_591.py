import os, re, smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

# ✅ 台北市、新北市區域對照表（section ID）
DISTRICT_SECTION = {
    # 台北市
    "中正區": 1, "大同區": 2, "中山區": 3, "松山區": 4,
    "大安區": 5, "萬華區": 6, "信義區": 7, "士林區": 8,
    "北投區": 9, "內湖區": 10, "南港區": 11, "文山區": 12,
    # 新北市
    "板橋區": 26, "新莊區": 44, "中和區": 38, "三重區": 43,
    "新店區": 34, "土城區": 39, "永和區": 37
}

# ✅ 初始化 Firebase
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
firebase_admin.initialize_app(credentials.Certificate(cred_dict))
db = firestore.client()

# ✅ 根據條件組出 591 搜尋 URL
def build_url(cond: dict) -> str:
    city_region_map = {
        "台北市": 1,
        "新北市": 3
    }
    region = city_region_map.get(cond["city"], 1)
    url = f"https://rent.591.com.tw/list?region={region}"
    section = DISTRICT_SECTION.get(cond["district"])
    if section:
        url += f"&section={section}"
    url += f"&price={cond['minPrice']}${cond['maxPrice']}$"
    url += f"&acreage={cond['minSize']}${cond['maxSize']}$"
    if cond.get("allowPets"):
        url += "&other=pet"
    return url

# ✅ 用 Playwright 拿下整頁 HTML
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

# ✅ 從 HTML 解析出房源資訊
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
        is_recent = False
        if "分鐘內更新" in updated:
            is_recent = True
        else:
            match = re.search(r"(\d+)小時內更新", updated)
            is_recent = match and int(match.group(1)) <= 3
        if is_recent:
            results.append({"title": title, "link": link, "updated": updated})
    return results

# ✅ 寫入 Firebase 的通知資料（使用者子集合方式）
def write_notifications(user_id, condition_id, listings):
    for l in listings:
        db.collection("users").document(user_id).collection("notifications").add({
            "conditionId": condition_id,
            "title": l["title"],
            "link": l["link"],
            "updated": l["updated"],
            "createdAt": firestore.SERVER_TIMESTAMP
        })

# ✅ 根據 userId 查詢 Email
def get_user_email(user_id):
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict().get("email")
    except Exception as e:
        print(f"⚠️ 無法查詢 email：{e}")
    return None

# ✅ 發送 Email 通知
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

# ✅ 刪除使用者原有的通知（子集合版本）
def delete_user_notifications(user_id):
    try:
        notifications_ref = db.collection("users").document(user_id).collection("notifications")
        docs = notifications_ref.stream()
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        print(f"🗑️ 已刪除使用者 {user_id} 的所有通知，共 {count} 筆")
    except Exception as e:
        print(f"⚠️ 無法刪除通知紀錄：{e}")

# ✅ 主流程
def main():
    cond_docs = db.collection("conditions").stream()
    for doc in cond_docs:
        cond = doc.to_dict()
        user_id = cond.get("userId")
        if not user_id:
            print("⚠️ 此條件缺少 userId，略過")
            continue
        if cond.get("city") not in ["台北市", "新北市"]:
            continue
        url = build_url(cond)
        print(f"🔍 查詢條件網址: {url}")
        soup = get_page_content(url)
        listings = parse_items(soup)
        print(f"→ 符合條件房源數量：{len(listings)}")

        if listings:
            delete_user_notifications(user_id)
            print(f"📥 寫入 {len(listings)} 條通知到 Firebase")
            write_notifications(user_id, doc.id, listings)
            email = get_user_email(user_id)
            if email:
                print(f"✅ 找到 email: {email}，準備寄信...")
                send_email(email, len(listings))
            else:
                print(f"❌ 找不到使用者 {user_id} 的 email")
    print("🎉 爬蟲完成，已寫入 Firebase 並寄送通知")
