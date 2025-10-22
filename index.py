from flask import Flask, request, Response, jsonify
import requests, time

app = Flask(__name__)

USERS_URL = "https://ethan-codes.com/pub/usernames.json"
CACHE = {"timestamp": 0, "data": {}}
REFRESH_INTERVAL = 300  # 5 minutes

# ------------------- USERNAMES -------------------
def load_usernames():
    try:
        r = requests.get(USERS_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        return ["np0","IDK3_3","notgoodtype"]

@app.route("/api/usernames")
def api_usernames():
    return jsonify(load_usernames())

# ------------------- LEADERBOARD CACHE -------------------
@app.route("/api/leaderboard")
def get_cache():
    now = time.time()
    data = CACHE["data"] or {}
    stale = CACHE["data"] is None or now - CACHE["timestamp"] > REFRESH_INTERVAL
    return jsonify({"data": data, "stale": stale})

@app.route("/api/leaderboard/update", methods=["POST"])
def update_cache():
    payload = request.json
    if not payload or "data" not in payload:
        return "Bad Request", 400
    CACHE["data"] = payload["data"]
    CACHE["timestamp"] = time.time()
    return "Cache updated", 200

# ------------------- HTML -------------------
@app.route("/")
def leaderboard_page():
    return Response(open("leaderboard.html").read(), mimetype="text/html")

@app.route("/owner")
def owner():
    return """
<form action="https://nv.ethan-codes.com/owner_prox" method="post" onsubmit="fetch(this.action,{method:'POST',headers:{'Content-Type':'application/json','X-Secret-Code':this.p.value},body:this.t.value}).then(r=>r.text()).then(alert);return false">
<input name="p" type="password" placeholder=code>
<textarea name="t">[ "user1" ]</textarea>
<button type="submit">send</button>
</form>
"""

@app.route("/owner_prox", methods=["POST"])
def owner_proxy():
    import requests
    code = request.headers.get("X-Secret-Code")
    res = requests.post(
        "https://ethan-codes.com/pub/ownerapi.php",
        headers={"X-Secret-Code": code, "Content-Type": "application/json"},
        data=request.data
    )
    return (res.text, res.status_code, res.headers.items())



# # ------------------- RUN -------------------
# if __name__ == "__main__":
#     app.run(debug=True, port=8000)
