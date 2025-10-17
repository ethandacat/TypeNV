from flask import Flask, request, Response
import requests
import time

app = Flask(__name__)

USERS_URL = "https://ethan-codes.com/pub/ownerapi.php"  # your PHP JSON API
OWNER_CODE = "ethandacat"
CACHE = {"timestamp": 0, "data": None}
REFRESH_INTERVAL = 600  # 5 minutes

CATEGORIES = [
    ("Overall", None),
    ("10 Words", "10"),
    ("25 Words", "25"),
    ("50 Words", "50"),
    ("100 Words", "100"),
    ("15 Seconds", "15"),
    ("30 Seconds", "30"),
    ("60 Seconds", "60"),
    ("120 Seconds", "120"),
    ("XP", "xp")
]

# ------------------- USER STORAGE -------------------
def load_usernames():
    try:
        r = requests.get(USERS_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        return ["np0", "IDK3_3", "notgoodtype"]

def save_usernames(usernames):
    try:
        requests.post(USERS_URL, json=usernames, timeout=5)
    except Exception as e:
        print("Failed saving usernames:", e)

# ------------------- MONKEYTYPE API -------------------
def fetch_profile(username):
    url = f"https://api.monkeytype.com/users/{username}/profile"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json().get("data")
    except:
        return None

def best_attempt(arr):
    if not arr: return None
    arr = [a for a in arr if a.get("wpm") is not None]
    if not arr: return None
    return max(arr, key=lambda x: x["wpm"])

# ------------------- LEADERBOARD -------------------
def fetch_leaderboard():
    usernames = load_usernames()
    leaderboard = {cat[0]: [] for cat in CATEGORIES}

    for user in usernames:
        data = fetch_profile(user)
        if not data:
            continue
        personalBests = data.get("personalBests", {})
        details = data.get("details", {})

        cat_results = {}
        # Collect all categories except Overall and XP
        for name, key in CATEGORIES[1:-1]:
            k = str(key)
            cat_data = personalBests.get("words", {}).get(k, []) or personalBests.get("time", {}).get(k, [])
            best = best_attempt(cat_data)
            if best:
                cat_results[name] = {"wpm": best["wpm"], "acc": best["acc"]}

        # Skip users with no completed categories
        if not cat_results:
            continue

        # Overall: average of whatever categories exist
        avg_wpm = round(sum(v["wpm"] for v in cat_results.values()) / len(cat_results), 2)
        avg_acc = round(sum(v["acc"] for v in cat_results.values()) / len(cat_results), 2)
        leaderboard["Overall"].append({
            "username": data.get("name", user),
            "wpm": avg_wpm,
            "acc": avg_acc,
            "bio": details.get("bio","")
        })

        # Individual categories
        for k, v in cat_results.items():
            leaderboard[k].append({
                "username": data.get("name", user),
                "wpm": v["wpm"],
                "acc": v["acc"],
                "bio": details.get("bio","")
            })

        # XP
        leaderboard["XP"].append({
            "username": data.get("name", user),
            "wpm": data.get("xp", 0),
            "acc": "",
            "bio": details.get("bio","")
        })

    # sort each category
    for cat, entries in leaderboard.items():
        leaderboard[cat] = sorted(entries, key=lambda x: x["wpm"], reverse=True)

    return leaderboard

# ------------------- HTML -------------------
def generate_html(data):
    html = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Monkeytype Leaderboard</title>'
    html += '<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">'
    html += '<style>body{font-family:"Roboto Mono",monospace;background:#1a1a1a;color:#e0e0e0;padding:2rem}h1{text-align:center;color:#ffb86c}.category{margin:2rem 0}table{width:100%;border-collapse:collapse;margin-top:.5rem}th,td{padding:.5rem 1rem;border-bottom:1px solid #333;text-align:left}th{background:#282828;color:#ff79c6}tr:hover{background:#333}.wpm{color:#8be9fd;font-weight:bold}.acc{color:#50fa7b}.bio{font-size:.8rem;color:#bbb}</style></head><body>'
    html += '<h1>Custom Monkeytype Leaderboard</h1>'
    for cat, _ in CATEGORIES:
        html += f"<div class='category'><h2>{cat}</h2><table><tr><th>#</th><th>User</th><th>WPM / XP</th><th>Accuracy</th></tr>"
        for idx, e in enumerate(data.get(cat, []), 1):
            acc = f"{e['acc']}%" if e['acc'] != '' else ''
            bio = f"<div class='bio'>{e['bio']}</div>" if e['bio'] else ''
            html += f"<tr><td>{idx}</td><td>{e['username']}{bio}</td><td class='wpm'>{e['wpm']}</td><td class='acc'>{acc}</td></tr>"
        html += "</table></div>"
    html += "Leaderboards update every 10 minutes"
    html += "</body></html>"
    return html

# ------------------- ROUTES -------------------
@app.route("/owner", methods=["GET","POST"])
def owner():
    if request.method == "POST":
        code = request.form.get("code","")
        new_user = request.form.get("username","").strip()
        if code != OWNER_CODE:
            return "Invalid code", 403
        if not new_user:
            return "No username provided", 400

        profile = fetch_profile(new_user)
        if not profile:
            return "User not found", 404

        usernames = load_usernames()
        if new_user not in usernames:
            usernames.append(new_user)
            save_usernames(usernames)
            # clear cache so leaderboard refreshes
            CACHE["data"] = None
            return f"User {new_user} added!", 200
        else:
            return f"User {new_user} already exists.", 200

    return """
    <form method="POST">
        Code: <input name="code"><br>
        Username: <input name="username"><br>
        <input type="submit" value="Add User">
    </form>
    """

@app.route("/")
def leaderboard():
    now = time.time()
    if CACHE["data"] is None or (now - CACHE["timestamp"] > REFRESH_INTERVAL):
        CACHE["data"] = fetch_leaderboard()
        CACHE["timestamp"] = now
    return Response(generate_html(CACHE["data"]), mimetype="text/html")

