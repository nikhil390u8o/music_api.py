from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)  # Allow frontend to fetch API

@app.route('/song')
def song():
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'Missing ?q='}), 400

    try:
        ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search = ydl.extract_info(f"ytsearch5:{q}", download=False)
            entries = search.get('entries', [])

            # Find the first playable public video
            info = None
            for e in entries:
                if e.get('url') and not e.get('age_limit', 0):
                    info = e
                    break

            if not info:
                return jsonify({'error': 'No playable public video found'}), 404

            return jsonify({
                'title': info['title'],
                'url': info['url'],
                'thumbnail': info['thumbnail'],
                'webpage_url': info['webpage_url']
            })

    except Exception as e:
        return jsonify({'error': 'Failed to fetch song', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
