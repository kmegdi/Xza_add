from flask import Flask, request, jsonify, render_template
import threading, time, requests, os, json, logging
from datetime import datetime
from byte import Encrypt_ID, encrypt_api  # تأكد من وجود هذا الملف

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

users_file = "users.json"
TOKEN = None

def get_author_info():
    return "API BY : XZANJA"

def fetch_token():
    url = "https://aditya-jwt-v11op.onrender.com/token?uid=3831627617&password=CAC2F2F3E2F28C5F5944D502CD171A8AAF84361CDC483E94955D6981F1CFF3E3"
    try:
        response = requests.get(url)
        print("📡 استجابة API الكاملة:", response.text)
        if response.status_code == 200:
            token = response.text.strip()
            if token.count('.') == 2:
                print("✅ تم جلب التوكن بنجاح:", token)
                return token
            else:
                print("⚠️ التوكن غير صالح (ليس JWT):", token)
                return None
        else:
            print(f"⚠️ فشل في جلب التوكن، كود الخطأ: {response.status_code}, الرد: {response.text}")
            return None
    except Exception as e:
        print("⚠️ خطأ أثناء جلب التوكن:", e)
        return None

def update_token():
    global TOKEN
    while True:
        new_token = fetch_token()
        if new_token:
            TOKEN = new_token
            print("🔄 تم تحديث التوكن بنجاح!")
        else:
            print("⚠️ لم يتم تحديث التوكن، سيتم المحاولة لاحقًا.")
        time.sleep(5 * 60 * 60)

def save_user(uid):
    users = {}
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    now = int(time.time())
    expiry = now + 86400
    users[uid] = {
        "added_at": now,
        "expires_at": expiry
    }
    with open(users_file, "w") as f:
        json.dump(users, f)

def clean_expired_uids():
    if not os.path.exists(users_file):
        return {}
    with open(users_file, "r") as f:
        users = json.load(f)
    now = int(time.time())
    users = {uid: data for uid, data in users.items() if data["expires_at"] > now}
    with open(users_file, "w") as f:
        json.dump(users, f)
    return users

def format_remaining_time(expiry_time):
    remaining = int(expiry_time - time.time())
    if remaining <= 0:
        return "⛔ Expired"
    days = remaining // 86400
    hours = (remaining % 86400) // 3600
    minutes = (remaining % 3600) // 60
    return f"{days} day(s) / {hours} hour(s) / {minutes} minute(s)"

def send_friend_request(player_id):
    if not TOKEN:
        return "🚫 Token not available. Try again later."
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
    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            return True
        else:
            return f"⚠️ Request failed: {response.status_code}\n📩 {response.text}"
    except Exception as e:
        return f"🚫 Error sending request: {str(e)}"

@app.route("/panel_add;", methods=["GET", "POST"])
def send_friend():
    try:
        uid = request.args.get("uid") if request.method == "GET" else request.json.get("uid")
        if not uid:
            return jsonify({"error": "UID is required.", "developer": get_author_info()}), 400

        result = send_friend_request(uid)
        if result is not True:
            return jsonify({"result": result, "developer": get_author_info()}), 400

        save_user(uid)
        now = int(time.time())
        expires = now + 86400

        return jsonify({
            "status": "✅ Friend request sent successfully.",
            "UID": uid,
            "added_at": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_time": format_remaining_time(expires),
            "expires_at": datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "1 day only",
            "developer": get_author_info()
        })
    except Exception as e:
        app.logger.error("❌ Error in /send_friend: %s", e, exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))