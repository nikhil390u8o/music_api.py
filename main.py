from flask import Flask, request, jsonify, Response
import requests
import urllib.parse
import re

app = Flask(__name__)

def get_youtube_url(query):
    instances = [
        "https://inv.tux.pizza",
        "https://invidious.nerdvpn.de",
        "https://invidious.privacydev.net",
        "https://yt.cdaut.de",
    ]
    for instance in instances:
        try:
            resp = requests.get(
                f"{instance}/api/v1/search",
                params={"q": query, "type": "video"},
                timeout=8
            )
            if resp.status_code == 200:
                results = resp.json()
                if results and isinstance(results, list):
                    video_id = results[0].get('videoId')
                    if video_id:
                        return f"https://www.youtube.com/watch?v={video_id}", video_id
        except:
            continue

    # Fallback: YouTube scrape
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        encoded = urllib.parse.quote(query)
        resp = requests.get(
            f"https://www.youtube.com/results?search_query={encoded}",
            headers=headers, timeout=10
        )
        ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
        if ids:
            return f"https://www.youtube.com/watch?v={ids[0]}", ids[0]
    except:
        pass

    return None, None


def get_direct_url(video_id: str, want_video: bool = False):
    """Get direct CDN URL from the worker API."""
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    fmt = "mp4hd" if want_video else "mp3"
    try:
        resp = requests.get(
            "https://youtube.anshppt19.workers.dev/anshapi",
            params={"url": yt_url, "format": fmt},
            timeout=30
        )
        data = resp.json().get("data", {})
        return data.get("url_mp4_youtube", "")
    except:
        return ""


@app.route('/query')
def query():
    q = request.args.get('q', '')
    if not q:
        return jsonify({"error": "q parameter missing"}), 400

    yt_url, video_id = get_youtube_url(q)
    if not yt_url:
        return jsonify({"error": "No video found"}), 404

    thumbnails = {
        "default": f"https://img.youtube.com/vi/{video_id}/default.jpg",
        "medium":  f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        "high":    f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        "max":     f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
    }

    mp4_data = {}
    try:
        resp = requests.get(
            "https://youtube.anshppt19.workers.dev/anshapi",
            params={"url": yt_url, "format": "mp4hd"},
            timeout=30
        )
        mp4_data = resp.json().get("data", {})
    except:
        pass

    mp3_data = {}
    try:
        resp = requests.get(
            "https://youtube.anshppt19.workers.dev/anshapi",
            params={"url": yt_url, "format": "mp3"},
            timeout=30
        )
        mp3_data = resp.json().get("data", {})
    except:
        pass

    return jsonify({
        "success": True,
        "yt_url": yt_url,
        "video_id": video_id,
        "thumbnails": thumbnails,
        "video": mp4_data,
        "audio": mp3_data
    })


@app.route('/stream')
def stream():
    """
    Render server se CDN URL proxy karke bot ko file bhejo.
    Usage: /stream?id=VIDEO_ID&type=video  or  &type=audio
    """
    video_id = request.args.get('id', '')
    want_video = request.args.get('type', 'audio') == 'video'

    if not video_id:
        return jsonify({"error": "id parameter missing"}), 400

    cdn_url = get_direct_url(video_id, want_video=want_video)
    if not cdn_url:
        return jsonify({"error": "Could not get CDN URL"}), 404

    # Proxy the file from Render's IP (same IP that generated the URL)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36",
        "Range": "bytes=0-",
    }
    try:
        cdn_resp = requests.get(cdn_url, headers=headers, stream=True, timeout=600)
        if cdn_resp.status_code not in (200, 206):
            return jsonify({"error": f"CDN returned {cdn_resp.status_code}"}), 502

        content_type = "video/mp4" if want_video else "audio/mpeg"

        def generate():
            for chunk in cdn_resp.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            status=cdn_resp.status_code,
            content_type=content_type,
            headers={
                "Content-Length": cdn_resp.headers.get("Content-Length", ""),
                "Accept-Ranges": "bytes",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)
