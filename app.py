import os
from threading import Lock
from flask import Flask, request, jsonify, session, redirect, render_template_string

app = Flask(__name__)

# Hosting ko Environment Variables ma set garnu
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")

lock = Lock()

queue = []
current_index = -1
playing = False
volume = 70


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Music Server</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            margin: 0;
            padding: 20px;
        }

        .box {
            max-width: 600px;
            margin: auto;
        }

        h1 {
            text-align: center;
        }

        input {
            width: 100%;
            box-sizing: border-box;
            padding: 14px;
            margin: 8px 0;
            border-radius: 10px;
            border: 1px solid #444;
            background: #222;
            color: white;
            font-size: 16px;
        }

        button {
            padding: 13px 17px;
            margin: 5px;
            border: 0;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
        }

        .controls {
            text-align: center;
            margin: 20px 0;
        }

        .add {
            width: 100%;
        }

        #status {
            background: #222;
            padding: 15px;
            border-radius: 12px;
            margin: 15px 0;
        }

        li {
            margin: 10px 0;
            padding: 10px;
            background: #222;
            border-radius: 8px;
            word-break: break-all;
        }

        .remove {
            float: right;
            background: #c62828;
            color: white;
        }

        input[type=range] {
            width: 100%;
        }
    </style>
</head>

<body>

<div class="box">

<h1>🎵 Music Server</h1>

<div id="status">
    Loading...
</div>

<input id="url" type="url"
       placeholder="YouTube URL राख्नुहोस्">

<button class="add" onclick="addSong()">
    ➕ Add to Queue
</button>

<div class="controls">
    <button onclick="control('previous')">⏮️</button>
    <button onclick="control('toggle')">▶️ / ⏸️</button>
    <button onclick="control('next')">⏭️</button>
</div>

<h3>🔊 Volume</h3>

<input
    type="range"
    min="0"
    max="100"
    value="70"
    onchange="setVolume(this.value)"
>

<h3>🎵 Queue</h3>

<ul id="queue"></ul>

</div>

<script>

async function api(url, options={}) {
    const r = await fetch(url, options);

    if (r.status === 401) {
        window.location.href = "/login";
        return null;
    }

    return await r.json();
}


async function loadStatus() {

    const data = await api("/api/status");

    if (!data) return;

    let current = "None";

    if (data.current) {
        current = data.current;
    }

    document.getElementById("status").innerHTML =
        "<b>Current:</b> " + current +
        "<br><b>Status:</b> " +
        (data.playing ? "▶️ Playing" : "⏸️ Paused") +
        "<br><b>Volume:</b> " + data.volume + "%";

    const list = document.getElementById("queue");
    list.innerHTML = "";

    data.queue.forEach((song, index) => {

        const li = document.createElement("li");

        li.innerHTML =
            (index + 1) + ". " +
            song +
            ' <button class="remove" onclick="removeSong(' +
            index +
            ')">✕</button>';

        list.appendChild(li);
    });
}


async function addSong() {

    const input = document.getElementById("url");
    const url = input.value.trim();

    if (!url) {
        alert("YouTube URL राख्नुहोस्");
        return;
    }

    const data = await api("/api/queue", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url: url
        })
    });

    if (data && data.error) {
        alert(data.error);
        return;
    }

    input.value = "";
    loadStatus();
}


async function control(action) {

    await api("/api/control", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            action: action
        })
    });

    loadStatus();
}


async function setVolume(value) {

    await api("/api/volume", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            volume: Number(value)
        })
    });

    loadStatus();
}


async function removeSong(index) {

    await api("/api/queue/" + index, {
        method: "DELETE"
    });

    loadStatus();
}


loadStatus();

setInterval(loadStatus, 2000);

</script>

</body>
</html>
"""


LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Music Server Login</title>

<style>
body {
    background:#111;
    color:white;
    font-family:Arial;
    padding:30px;
}

.box {
    max-width:400px;
    margin:auto;
}

input,button {
    width:100%;
    box-sizing:border-box;
    padding:14px;
    margin:8px 0;
    border-radius:10px;
    font-size:16px;
}

input {
    background:#222;
    color:white;
    border:1px solid #444;
}

button {
    background:#fff;
    border:0;
}
</style>

</head>

<body>

<div class="box">

<h2>🔐 Music Server Login</h2>

<form method="POST">

<input
    type="password"
    name="password"
    placeholder="Password"
    required
>

<button type="submit">
    Login
</button>

</form>

{% if error %}
<p>{{ error }}</p>
{% endif %}

</div>

</body>
</html>
"""


def logged_in():
    return session.get("logged_in") is True


def auth_required():
    if not logged_in():
        return jsonify({
            "error": "Unauthorized"
        }), 401


@app.route("/")
def home():

    if not logged_in():
        return redirect("/login")

    return render_template_string(HTML)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        password = request.form.get("password", "")

        if password == ADMIN_PASSWORD:

            session["logged_in"] = True

            return redirect("/")

        return render_template_string(
            LOGIN_HTML,
            error="Wrong password"
        )

    return render_template_string(
        LOGIN_HTML,
        error=""
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


@app.route("/api/status")
def status():

    if not logged_in():
        return jsonify({
            "error": "Unauthorized"
        }), 401

    with lock:

        current = None

        if 0 <= current_index < len(queue):
            current = queue[current_index]

        return jsonify({
            "queue": queue,
            "current": current,
            "current_index": current_index,
            "playing": playing,
            "volume": volume
        })


@app.route("/api/queue", methods=["POST"])
def add_to_queue():

    result = auth_required()

    if result:
        return result

    data = request.get_json(silent=True) or {}

    url = data.get("url", "").strip()

    if not url:
        return jsonify({
            "error": "URL आवश्यक छ"
        }), 400

    # Basic YouTube URL check
    if not (
        "youtube.com/" in url
        or "youtu.be/" in url
    ):
        return jsonify({
            "error": "YouTube URL मात्र राख्नुहोस्"
        }), 400

    with lock:

        queue.append(url)

        global current_index

        if current_index == -1:
            current_index = 0

    return jsonify({
        "success": True,
        "queue": queue
    })


@app.route("/api/queue/<int:index>", methods=["DELETE"])
def remove_from_queue(index):

    result = auth_required()

    if result:
        return result

    global current_index

    with lock:

        if index < 0 or index >= len(queue):

            return jsonify({
                "error": "Invalid queue item"
            }), 404

        queue.pop(index)

        if not queue:

            current_index = -1

        elif current_index >= len(queue):

            current_index = len(queue) - 1

    return jsonify({
        "success": True,
        "queue": queue
    })


@app.route("/api/control", methods=["POST"])
def control():

    result = auth_required()

    if result:
        return result

    global current_index
    global playing

    data = request.get_json(silent=True) or {}

    action = data.get("action")

    with lock:

        if action == "toggle":

            playing = not playing

        elif action == "next":

            if queue:

                if current_index < len(queue) - 1:
                    current_index += 1
                else:
                    current_index = 0

                playing = True

        elif action == "previous":

            if queue:

                if current_index > 0:
                    current_index -= 1
                else:
                    current_index = len(queue) - 1

                playing = True

        elif action == "play":

            playing = True

        elif action == "pause":

            playing = False

        else:

            return jsonify({
                "error": "Unknown action"
            }), 400

    return jsonify({
        "success": True,
        "action": action
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
    except:
        value = 70

    value = max(0, min(100, value))

    with lock:
        volume = value

    return jsonify({
        "success": True,
        "volume": volume
    })


@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "service": "music-server"
    })


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
        )
