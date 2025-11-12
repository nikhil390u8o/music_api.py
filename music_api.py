from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/song')
def song():
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'Missing ?q='}), 400

    opts = {'format': 'bestaudio'}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{q}", download=False)['entries'][0]
        return jsonify({
            'title': info['title'],
            'url': info['url'],
            'thumbnail': info['thumbnail'],
            'webpage_url': info['webpage_url']
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1470)
