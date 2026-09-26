import os
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__, static_folder='.', template_folder='.')

# হোমপেজ রেন্ডার
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# পিং বট রুট (সার্ভার ২৪ ঘণ্টা জাগিয়ে রাখার জন্য)
@app.route('/ping')
def ping():
    return jsonify({'status': 'active', 'server': 'PRINCE SHUVO ENGINE'})

# ডাউনলোডার ব্যাকএন্ড এপিআই
@app.route('/api/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'দয়া করে একটি সঠিক ভিডিও লিংক দিন'}), 400

    # yt-dlp কনফিগারেশন (ভিডিও ডাউনলোড না করে সরাসরি ডিরেক্ট লিংক বের করবে)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'format': 'best[ext=mp4]/best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # প্লেলিস্ট হলে প্রথম ভিডিও নিবে
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'HD Video Stream')
            cover = info.get('thumbnail', '')
            author = info.get('uploader') or info.get('creator') or info.get('channel') or 'Verified Media'
            
            # ডিরেক্ট ভিডিও লিংক
            video_url = info.get('url')
            
            if not video_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url') and (f.get('vcodec') != 'none'):
                        video_url = f.get('url')
                        break
            
            # অডিও লিংক বের করা
            audio_url = None
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('url') and f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        audio_url = f.get('url')
                        break

            if not video_url:
                return jsonify({'error': 'ভিডিওর ডাউনলোড লিংক পাওয়া যায়নি'}), 404

            return jsonify({
                'success': True,
                'title': title,
                'cover': cover,
                'videoUrl': video_url,
                'audioUrl': audio_url,
                'author': author
            })

    except Exception as e:
        return jsonify({'error': f'সার্ভার এরর: লিংকটি সঠিক কি না যাচাই করুন'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
