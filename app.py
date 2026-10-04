
import os
from threading import Lock
from urllib.parse import urlparse

from flask import (
    Flask,
    request,
    jsonify,
    session,
    redirect,
    render_template_string,
)

app = Flask(__name__)

# Set these in your hosting provider's environment variables.
SECRET_KEY = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not SECRET_KEY or not ADMIN_PASSWORD:
    raise RuntimeError(
        "Please set SECRET_KEY and ADMIN_PASSWORD "
        "in your hosting environment."
    )

app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,  # Requires HTTPS
)

lock = Lock()

queue = []
current_index = -1
playing = False
volume = 70

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Music Server</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0; padding: 20px;
    background: #111; color: #fff;
    font-family: Arial, sans-serif;
}
.box { max-width: 600px; margin: auto; }
h1 { text-align: center; }
input, button {
    padding: 13px; border-radius: 10px;
    font-size: 16px;
}
input {
    width: 100%; margin: 8px 0;
    color: white; background: #222;
    border: 1px solid #444;
}
button { border: 0; margin: 4px; cursor: pointer; }
.add { width: 100%; background: #8ee6a8; }
.controls { text-align: center; margin: 18px 0; }
.controls button { min-width: 65px; }
#status {
    padding: 15px; background: #222;
    border-radius: 12px; overflow-wrap: anywhere;
}
li {
    margin: 10px 0; padding: 10px;
    background: #222; border-radius: 8px;
    overflow-wrap: anywhere;
}
.remove { float: right; background: #c62828; color: white; }
.notice { color: #ffd27d; font-size: 14px; line-height: 1.5; }
a { color: #9dcaff; }
</style>
</head>
<body>
<div class="box">
<h1>🎵 Music Server</h1>

<div id="status">Loading status...</div>

<p class="notice">
Control-panel prototype only. Playback and Clubhouse audio
are not connected yet.
</p>

<form id="addForm">
<input id="url" type="url"
 placeholder="Paste a YouTube URL" required>
<button class="add" type="submit">＋ Add to Queue</button>
</form>

<div class="controls">
<button type="button" onclick="control('previous')">⏮ Previous</button>
<button type="button" onclick="control('toggle')">▶ / ⏸</button>
<button type="button" onclick="control('next')">Next ⏭</button>
</div>

<h3>🔊 Volume: <span id="volumeLabel">70</span>%</h3>
<input id="volume" type="range" min="0" max="100" value="70">

<h3>🎶 Queue</h3>
<ul id="queue"></ul>

<p><a href="/logout">Log out</a></p>
</div>

<script>
async function api(path, options = {}) {
    const response = await fetch(path, {
        credentials: "same-origin",
        ...options
    });

    if (response.status === 401) {
        location.href = "/login";
        return null;
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}

async function loadStatus() {
    try {
        const data = await api("/api/status");
        if (!data) return;

        document.getElementById("status").textContent =
            "Current: " + (data.current || "None") +
            " | Status: " + (data.playing ? "Playing" : "Paused") +
            " | Volume: " + data.volume + "%";

        document.getElementById("volumeLabel").textContent = data.volume;
        document.getElementById("volume").value = data.volume;

        const list = document.getElementById("queue");
        list.replaceChildren();

        data.queue.forEach((song, index) => {
            const li = document.createElement("li");
            li.append(document.createTextNode((index + 1) + ". " + song + " "));

            const remove = document.createElement("button");
            remove.className = "remove";
            remove.textContent = "Remove";
            remove.onclick = () => removeSong(index);

            li.appendChild(remove);
            list.appendChild(li);
        });
    } catch (error) {
        console.error(error);
    }
}

document.getElementById("addForm").addEventListener("submit", async event => {
    event.preventDefault();

    const input = document.getElementById("url");

    try {
        await api("/api/queue", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url: input.value.trim()})
        });
        input.value = "";
        await loadStatus();
    } catch (error) {
        alert(error.message);
    }
});

async function control(action) {
    try {
        await api("/api/control", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({action})
        });
        await loadStatus();
    } catch (error) {
        alert(error.message);
    }
}

document.getElementById("volume").addEventListener("change", async event => {
    try {
        await api("/api/volume", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({volume: Number(event.target.value)})
        });
        await loadStatus();
    } catch (error) {
        alert(error.message);
    }
});

async function removeSong(index) {
    try {
        await api("/api/queue/" + index, {method: "DELETE"});
        await loadStatus();
    } catch (error) {
        alert(error.message);
    }
}

loadStatus();
setInterval(loadStatus, 5000);
</script>
</body>
</html>
"""

LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Music Server Login</title>
<style>
body {
    margin: 0; padding: 30px;
    background: #111; color: white;
    font-family: Arial, sans-serif;
}
.box { max-width: 400px; margin: auto; }
input, button {
    width: 100%; padding: 14px;
    margin: 8px 0; border-radius: 10px;
    font-size: 16px; box-sizing: border-box;
}
input { background: #222; color: white; border: 1px solid #444; }
button { background: white; color: black; border: 0; }
.error { color: #ff8a80; }
</style>
</head>
<body>
<div class="box">
<h2>🔐 Music Server Login</h2>
<form method="post">
<input type="password" name="password"
 placeholder="Admin password" required autocomplete="current-password">
<button type="submit">Login</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
</div>
</body>
</html>
"""


def logged_in():
    return session.get("logged_in") is True


def auth_required():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    return None


def valid_youtube_url(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        allowed_hosts = {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "music.youtube.com",
            "youtu.be",
            "www.youtu.be",
        }
        return (
            parsed.scheme == "https"
            and host in allowed_hosts
            and bool(parsed.path.strip("/"))
        )
    except (ValueError, AttributeError):
        return False


@app.route("/")
def home():
    if not logged_in():
        return redirect("/login")
    return render_template_string(HTML)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")

        if password and password == ADMIN_PASSWORD:
            session.clear()
            session["logged_in"] = True
            session.permanent = False
            return redirect("/")

        return render_template_string(
            LOGIN_HTML, error="Incorrect password"
        ), 401

    return render_template_string(LOGIN_HTML, error="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/api/status")
def status():
    result = auth_required()
    if result:
        return result

    with lock:
        current = (
            queue[current_index]
            if 0 <= current_index < len(queue)
            else None
        )
        return jsonify({
            "queue": list(queue),
            "current": current,
            "current_index": current_index,
            "playing": playing,
            "volume": volume,
            "playback_connected": False,
            "message": "Control panel only; no audio engine connected.",
        })


@app.route("/api/queue", methods=["POST"])
def add_to_queue():
    result = auth_required()
    if result:
        return result

    data = request.get_json(silent=True) or {}
    url = data.get("url", "")

    if not isinstance(url, str):
        return jsonify({"error": "URL must be text"}), 400

    url = url.strip()

    if not valid_youtube_url(url):
        return jsonify({"error": "Enter a valid HTTPS YouTube URL"}), 400

    with lock:
        queue.append(url)
        global current_index
        if current_index == -1:
            current_index = 0

    return jsonify({"success": True, "queue": list(queue)})


@app.route("/api/queue/<int:index>", methods=["DELETE"])
def remove_from_queue(index):
    result = auth_required()
    if result:
        return result

    global current_index, playing

    with lock:
        if not 0 <= index < len(queue):
            return jsonify({"error": "Queue item not found"}), 404

        queue.pop(index)

        if not queue:
            current_index = -1
            playing = False
        elif index < current_index:
            current_index -= 1
        elif index == current_index:
            current_index = min(index, len(queue) - 1)

    return jsonify({"success": True, "queue": list(queue)})


@app.route("/api/control", methods=["POST"])
def control():
    result = auth_required()
    if result:
        return result

    global current_index, playing

    data = request.get_json(silent=True) or {}
    action = data.get("action")

    with lock:
        if action == "toggle":
            playing = not playing if queue else False

        elif action == "play":
            playing = bool(queue)

        elif action == "pause":
            playing = False

        elif action == "next":
            if queue:
                current_index = (
                    0 if current_index >= len(queue) - 1
                    else current_index + 1
                )
                playing = True

        elif action == "previous":
            if queue:
                current_index = (
                    len(queue) - 1 if current_index <= 0
                    else current_index - 1
                )
                playing = True

        else:
            return jsonify({"error": "Unknown action"}), 400

    return jsonify({
        "success": True,
        "action": action,
        "message": "State updated; audio playback is not connected.",
    })


@app.route("/api/volume", methods=["POST"])
def set_volume():
    result = auth_required()
    if result:
        return result

    global volume

    data = request.get_json(silent=True) or {}

    try:
        value = int(data.get("volume", 70))
    except (ValueError, TypeError):
        return jsonify({"error": "Volume must be a number"}), 400

    value = max(0, min(100, value))

    with lock:
        volume = value

    return jsonify({
        "success": True,
        "volume": volume,
        "message": "Saved in control panel; audio engine not connected.",
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "service": "music-server-control-panel",
        "playback_connected": False,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
            
