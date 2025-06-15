"""
crawler_to_firebase_with_utils.py
從 Firebase「conditions」讀取條件 → 拼 591 URL → 爬 title/link → 寫入 notifications → 發送 email
"""

import time, sys, os, re, smtplib
from email.mime.text import MIMEText
from email.header import Header
import firebase_admin
from firebase_admin import credentials, firestore
import dotenv
dotenv.load_dotenv()

# === 導入你專案自訂 util ===
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from libs.utils import use_selenium, get_page_content

# === 區域代碼對照表（台北市 region=1）===
DISTRICT_SECTION = {
    "中正區": 1, "大同區": 2, "中山區": 3, "松山區": 4,
    "大安區": 5, "萬華區": 6, "信義區": 7, "士林區": 8,
    "北投區": 9, "內湖區": 10, "南港區": 11, "文山區": 12
}

# === 初始化 Firebase ===
cred = credentials.Certificate("firebase_service_account.json")  # 替換為你的憑證
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- 建立查詢 URL ----------
def build_url(cond: dict) -> str:
    url = "https://rent.591.com.tw/list?region=1"  # 台北市
    section = DISTRICT_SECTION.get(cond["district"])
    if section:
        url += f"&section={section}"
    url += f"&price={cond['minPrice']}${cond['maxPrice']}$"
    url += f"&acreage={cond['minSize']}${cond['maxSize']}$"
    if cond.get("allowPets"):
        url += "&other=pet"
    return url

# ---------- 解析爬到的項目 ----------
def parse_items(soup):
    results = []
    for item in soup.select(".list-wrapper .item"):
        title_tag = item.select_one("a.link")
        if not title_tag:
            continue

        title = title_tag.text.strip()
        link = title_tag["href"]

        # 找更新時間
        updated = ""
        for line in item.select("span.line"):
            text = line.get_text(strip=True)
            if "更新" in text:
                updated = text
                break

        # 僅保留 3 小時內更新
        if "分鐘內更新" in updated:
            is_recent = True
        else:
            match = re.search(r"(\d+)小時內更新", updated)
            is_recent = match and int(match.group(1)) <= 3

        if is_recent:
            results.append({
                "title": title,
                "link": link,
                "updated": updated
            })
    return results

# ---------- 寫入通知 ----------
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

# ---------- 根據 UID 查詢 email ----------
def get_user_email(user_id):
    try:
        doc_ref = db.collection("users").document(user_id)
        user_doc = doc_ref.get()
        if user_doc.exists:
            return user_doc.to_dict().get("email")
    except Exception as e:
        print(f"⚠️ 無法查詢 email：{e}")
    return None

# ---------- 發送 email ----------
def send_email(to_email, count):
    subject = "開 Home 爬：有新的房屋通知囉！"
    body = f"您好，系統剛為您找到了 {count} 間符合條件的房屋資訊，請至您的通知頁面查看。"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = "開 Home 爬 通知 <your@gmail.com>"
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))  # ⚠️ 替換！
            server.send_message(msg)
        print(f"📧 已寄信通知 {to_email}")
    except Exception as e:
        print(f"⚠️ 寄信失敗: {e}")

# ---------- 主流程 ----------
def main():
    driver = use_selenium()
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
        soup = get_page_content(driver, url)
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

    driver.quit()
    print("🎉 爬蟲完成，已寫入 Firebase 並寄送通知")

if __name__ == "__main__":
    main()
