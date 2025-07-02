from flask import Flask, request, jsonify
from datetime import datetime
import threading, time, requests, os, json, logging
from byte import Encrypt_ID, encrypt_api  # تأكد من وجود byte.py

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# ===== إعدادات عامة =====
users_file = "users.json"
TOKEN = None


# ===== معلومات المطور =====
def get_author_info():
    return "REMOVE API BY : XZANJA"


# ===== جلب التوكن من API خارجي =====
def fetch_token():
    url = "https://aditya-jwt-v11op.onrender.com/token?uid=3831627617&password=CAC2F2F3E2F28C5F5944D502CD171A8AAF84361CDC483E94955D6981F1CFF3E3"
    try:
        response = requests.get(url)
        app.logger.info("📡 استجابة API: %s", response.text)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "").strip()
            if token.count('.') == 2:
                app.logger.info("✅ تم جلب التوكن بنجاح: %s", token)
                return token
        app.logger.warning("⚠️ فشل جلب التوكن - %s", response.status_code)
    except Exception as e:
        app.logger.error("🚫 خطأ أثناء جلب التوكن: %s", str(e))
    return None


# ===== تحديث التوكن تلقائيًا =====
def update_token():
    global TOKEN
    while True:
        new_token = fetch_token()
        if new_token:
            TOKEN = new_token
            app.logger.info("🔄 تم تحديث التوكن.")
        time.sleep(1)


# ===== إزالة صديق =====
def remove_friend(player_id):
    if not TOKEN:
        return "🚫 التوكن غير متاح حاليًا، يرجى المحاولة لاحقًا."

    try:
        encrypted_id = Encrypt_ID(player_id)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)

        url = "https://clientbp.ggblueshark.com/RemoveFriend"
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
            return f"⚠️ فشل الحذف: {response.status_code} - {response.text}"
    except Exception as e:
        return f"🚫 خطأ أثناء الإرسال: {str(e)}"


# ===== واجهة API لإزالة صديق =====
@app.route("/panel_remove", methods=["GET", "POST"])
def api_remove_friend():
    try:
        uid = request.args.get("uid") if request.method == "GET" else request.json.get("uid")
        if not uid:
            return jsonify({"error": "UID مفقود", "developer": get_author_info()}), 400

        result = remove_friend(uid)
        if result is not True:
            return jsonify({"result": result, "developer": get_author_info()}), 400

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({
            "status": "✅ تم إزالة الصديق بنجاح.",
            "UID": uid,
            "timestamp": now,
            "developer": get_author_info()
        })
    except Exception as e:
        app.logger.error("❌ خطأ في /panel_remove: %s", e, exc_info=True)
        return jsonify({"error": "حدث خطأ داخلي", "details": str(e)}), 500


# ===== تشغيل الخادم =====
if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 18012)))