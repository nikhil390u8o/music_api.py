from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)  # Allow frontend to access API

@app.route('/song')
def song():
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'Missing ?q='}), 400

    try:
        ydl_opts = {'format': 'bestaudio/best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{q}", download=False)['entries'][0]
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
