from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>YouTube Music Server</title>

    <style>
        body {
            font-family: Arial;
            max-width: 600px;
            margin: 30px auto;
            padding: 20px;
            text-align: center;
        }

        input {
            width: 90%;
            padding: 12px;
            margin: 10px;
            box-sizing: border-box;
        }

        button {
            padding: 12px 18px;
            margin: 5px;
            border: 0;
            border-radius: 8px;
            cursor: pointer;
        }

        #player {
            margin-top: 20px;
        }

        #status {
            margin: 20px;
            font-weight: bold;
        }
    </style>
</head>

<body>

<h1>🎵 YouTube Music Server</h1>

<input
    id="url"
    type="text"
    placeholder="Paste YouTube link here"
>

<br>

<button onclick="loadYouTube()">🎵 Load</button>
<button onclick="playSong()">▶️ Play</button>
<button onclick="pauseSong()">⏸️ Pause</button>
<button onclick="stopSong()">⏹️ Stop</button>

<div id="player"></div>

<div id="status">Ready</div>

<script src="https://www.youtube.com/iframe_api"></script>

<script>

let player = null;
let pendingVideoId = null;

function getVideoId(url) {

    try {

        const u = new URL(url);

        if (u.hostname.includes("youtu.be")) {
            return u.pathname.substring(1);
        }

        if (u.hostname.includes("youtube.com")) {

            if (u.searchParams.get("v")) {
                return u.searchParams.get("v");
            }

            const parts = u.pathname.split("/");

            if (parts[1] === "shorts") {
                return parts[2];
            }

            if (parts[1] === "embed") {
                return parts[2];
            }
        }

    } catch (e) {
        return null;
    }

    return null;
}


function loadYouTube() {

    const url = document.getElementById("url").value.trim();

    const videoId = getVideoId(url);

    if (!videoId) {
        document.getElementById("status").innerText =
            "Invalid YouTube link ❌";
        return;
    }

    pendingVideoId = videoId;

    if (player) {

        player.loadVideoById(videoId);

        document.getElementById("status").innerText =
            "Loaded 🎵";

    } else {

        document.getElementById("status").innerText =
            "YouTube player loading...";
    }
}


function onYouTubeIframeAPIReady() {

    player = new YT.Player("player", {

        height: "315",
        width: "100%",

        videoId: pendingVideoId || "",

        playerVars: {
            playsinline: 1
        },

        events: {

            onReady: function() {

                document.getElementById("status").innerText =
                    "Player ready 🎵";

                if (pendingVideoId) {
                    player.loadVideoById(pendingVideoId);
                }
            },

            onStateChange: function(event) {

                if (event.data === YT.PlayerState.PLAYING) {
                    document.getElementById("status").innerText =
                        "Playing ▶️";
                }

                if (event.data === YT.PlayerState.PAUSED) {
                    document.getElementById("status").innerText =
                        "Paused ⏸️";
                }

                if (event.data === YT.PlayerState.ENDED) {
                    document.getElementById("status").innerText =
                        "Finished ✅";
                }
            }
        }
    });
}


function playSong() {

    if (player) {
        player.playVideo();
    }
}


function pauseSong() {

    if (player) {
        player.pauseVideo();
    }
}


function stopSong() {

    if (player) {
        player.stopVideo();
    }
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
    return "OK"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
                             )
