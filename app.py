from flask import Flask, request, jsonify
from datetime import datetime
import threading, time, requests, os, json, logging
from byte import Encrypt_ID, encrypt_api  # تأكد من وجود byte.py في نفس المجلد

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# ======== إعدادات عامة ========
users_file = "users.json"
TOKEN = None


# ======== معلومات المطور ========
def get_author_info():
    return "API BY : XZANJA"


# ======== جلب التوكن من API خارجي ========
def fetch_token():
    url = "https://jwt-gen-api-v2.onrender.com/token?uid=3831627617&password=CAC2F2F3E2F28C5F5944D502CD171A8AAF84361CDC483E94955D6981F1CFF3E3"
    try:
        response = requests.get(url)
        app.logger.info("📡 استجابة API: %s", response.text)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "").strip()
            if token.count('.') == 2:
                app.logger.info("✅ تم جلب التوكن بنجاح: %s", token)
                return token
            else:
                app.logger.warning("⚠️ التوكن غير صالح (ليس JWT): %s", token)
        else:
            app.logger.warning("⚠️ فشل جلب التوكن - الحالة: %s | %s", response.status_code, response.text)
    except Exception as e:
        app.logger.error("🚫 خطأ أثناء جلب التوكن: %s", str(e))
    return None


# ======== تحدّيث التوكن كل ثانية ========
def update_token():
    global TOKEN
    while True:
        new_token = fetch_token()
        if new_token:
            TOKEN = new_token
            app.logger.info("🔄 تم تحديث التوكن.")
        else:
            app.logger.warning("🔁 فشل تحديث التوكن.")
        time.sleep(1)  # تحديث كل ثانية


# ======== حفظ UID المستخدم لمدة يوم ========
def save_user(uid):
    users = {}
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            try:
                users = json.load(f)
            except:
                users = {}
    now = int(time.time())
    expiry = now + 86400
    users[uid] = {"added_at": now, "expires_at": expiry}
    with open(users_file, "w") as f:
        json.dump(users, f)


# ======== حساب الوقت المتبقي ========
def format_remaining_time(expiry_time):
    remaining = int(expiry_time - time.time())
    if remaining <= 0:
        return "⛔ Expired"
    days = remaining // 86400
    hours = (remaining % 86400) // 3600
    minutes = (remaining % 3600) // 60
    return f"{days}d / {hours}h / {minutes}m"


# ======== إرسال طلب صداقة ========
def send_friend_request(player_id):
    if not TOKEN:
        return "🚫 Token غير متوفر، حاول لاحقاً."
    try:
        encrypted_id = Encrypt_ID(player_id)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)
        url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB49",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(encrypted_payload)),
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
            "Host": "clientbp.ggblueshark.com",
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate, br"
        }
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            return True
        else:
            return f"⚠️ فشل الإرسال: {response.status_code} - {response.text}"
    except Exception as e:
        return f"🚫 خطأ أثناء الإرسال: {str(e)}"


# ======== نقطة API لإرسال الطلب ========
@app.route("/panel_add", methods=["GET", "POST"])
def send_friend():
    try:
        uid = request.args.get("uid") if request.method == "GET" else request.json.get("uid")
        if not uid:
            return jsonify({"error": "UID مطلوب", "developer": get_author_info()}), 400

        result = send_friend_request(uid)
        if result is not True:
            return jsonify({"result": result, "developer": get_author_info()}), 400

        save_user(uid)
        now = int(time.time())
        expires = now + 86400

        return jsonify({
            "status": "✅ تم إرسال الطلب بنجاح.",
            "UID": uid,
            "added_at": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_time": format_remaining_time(expires),
            "expires_at": datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "1 يوم فقط",
            "developer": get_author_info()
        })
    except Exception as e:
        app.logger.error("❌ خطأ في /panel_add: %s", e, exc_info=True)
        return jsonify({"error": "حدث خطأ داخلي", "details": str(e)}), 500


# ======== تشغيل الخادم ========
if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))