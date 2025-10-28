from flask import Flask, request, Response, jsonify
import requests, time, html

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
    return Response(open("leaderboard.html", encoding="utf-8").read(), mimetype="text/html")

@app.route("/profile/<username>")
def profile(username):
    with open("profile.html", encoding="utf-8") as f:
        html_content = f.read()
    html_content = html_content.replace("{{USERNAME}}", html.escape(username))
    return Response(html_content, mimetype="text/html")

@app.route("/owner")
def owner():
    p = requests.get("https://ethan-codes.com/pub/usernames.json").json()
    return """
<form id="f" action="/owner_prox" method="post">
  <input name="p" type="password" placeholder="code">
  <textarea name="t">"""+str(p)+"""</textarea>
  <button type="submit">send</button>
</form>
<script>
document.getElementById('f').addEventListener('submit', e => {
  e.preventDefault();
  fetch(e.target.action, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Secret-Code': e.target.p.value
    },
    body: e.target.t.value
  })
  .then(r => r.text())
  .then(alert)
  .catch(err => alert('Fetch error: ' + err));
});
</script>
"""


@app.route("/owner_prox", methods=["POST"])
def owner_proxy():
    code = request.headers.get("X-Secret-Code")
    res = requests.post(
        "https://ethan-codes.com/pub/ownerapi.php",
        headers={"X-Secret-Code": code, "Content-Type": "application/json"},
        data=request.data
    )
    return Response(res.text, status=res.status_code, headers=dict(res.headers))


# ------------------- RUN -------------------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
