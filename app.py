from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Music Server</title>
    <style>
        body {
            font-family: Arial;
            max-width: 500px;
            margin: 40px auto;
            padding: 20px;
            text-align: center;
        }

        input {
            width: 90%;
            padding: 12px;
            margin: 8px;
            box-sizing: border-box;
        }

        button {
            padding: 12px 18px;
            margin: 5px;
            border: 0;
            border-radius: 8px;
            cursor: pointer;
        }

        #status {
            margin: 20px;
            font-weight: bold;
        }

        audio {
            width: 100%;
            margin-top: 20px;
        }
    </style>
</head>

<body>

<h1>🎵 Music Server</h1>

<input id="url" type="url"
       placeholder="Direct MP3/audio URL">

<br>

<button onclick="loadSong()">🎵 Load</button>
<button onclick="playSong()">▶️ Play</button>
<button onclick="pauseSong()">⏸️ Pause</button>
<button onclick="stopSong()">⏹️ Stop</button>

<br><br>

<label>🔊 Volume</label>
<input id="volume"
       type="range"
       min="0"
       max="1"
       step="0.01"
       value="1"
       oninput="changeVolume(this.value)">

<audio id="player" controls></audio>

<div id="status">Ready</div>

<script>

const player = document.getElementById("player");
const statusBox = document.getElementById("status");

function loadSong() {

    const url = document.getElementById("url").value.trim();

    if (!url) {
        statusBox.innerText = "Please enter an audio URL";
        return;
    }

    player.src = url;
    player.load();

    statusBox.innerText = "Song loaded 🎵";
}

function playSong() {

    player.play()
        .then(() => {
            statusBox.innerText = "Playing 🎵";
        })
        .catch((error) => {
            statusBox.innerText = "Cannot play: " + error.message;
        });
}

function pauseSong() {

    player.pause();
    statusBox.innerText = "Paused ⏸️";
}

function stopSong() {

    player.pause();
    player.currentTime = 0;

    statusBox.innerText = "Stopped ⏹️";
}

function changeVolume(value) {

    player.volume = value;
}

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "status": "OK",
        "service": "Music Server"
    })


@app.route("/status")
def status():
    return jsonify({
        "running": True,
        "message": "Music server is running"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
