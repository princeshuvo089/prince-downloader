import os
import urllib.request
import urllib.parse
import json
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__, static_folder='.', template_folder='.')

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/ping')
def ping():
    return jsonify({'status': 'active', 'server': 'PRINCE SHUVO ENGINE'})

@app.route('/api/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'দয়া করে একটি সঠিক ভিডিও লিংক দিন'}), 400

    # কৌশল ১: টিকটক ভিডিওর জন্য পাইথন সুপারফাস্ট গেটওয়ে (কোনো ওয়াটারমার্ক থাকবে না)
    if 'tiktok.com' in url or 'douyin.com' in url:
        try:
            req_data = urllib.parse.urlencode({'url': url, 'hd': '1'}).encode('utf-8')
            req = urllib.request.Request(
                'https://www.tikwm.com/api/',
                data=req_data,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                if res_json.get('code') == 0 and 'data' in res_json:
                    v_data = res_json['data']
                    return jsonify({
                        'success': True,
                        'title': v_data.get('title') or 'TikTok Video (No Watermark)',
                        'cover': v_data.get('cover'),
                        'videoUrl': v_data.get('play'),
                        'audioUrl': v_data.get('music'),
                        'author': v_data.get('author', {}).get('nickname') or 'TikTok Creator'
                    })
        except Exception as te:
            print("TikWM error, falling back to yt-dlp:", te)

    # কৌশল ২: ইউটিউব, ফেসবুক, ইনস্টাগ্রাম ইত্যাদির জন্য yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'HD Video Stream')
            cover = info.get('thumbnail', '')
            author = info.get('uploader') or info.get('creator') or info.get('channel') or 'Verified Media'
            
            video_url = info.get('url')
            
            if not video_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url') and (f.get('vcodec') != 'none'):
                        video_url = f.get('url')
                        break
            
            audio_url = None
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('url') and f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        audio_url = f.get('url')
                        break

            if not video_url:
                return jsonify({'error': 'ভিডিওর ডিরেক্ট ডাউনলোড লিংক পাওয়া যায়নি'}), 404

            return jsonify({
                'success': True,
                'title': title,
                'cover': cover,
                'videoUrl': video_url,
                'audioUrl': audio_url,
                'author': author
            })

    except Exception as e:
        return jsonify({'error': f'লিংকটি পাবলিক কি না অথবা ভিডিওটি সঠিক কি না যাচাই করুন'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
