from flask import Flask, request, send_file, render_template_string, after_this_request
import yt_dlp
import uuid
import os
import tempfile
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Trình tải video</title>
</head>
<body style="font-family: sans-serif; padding: 2rem;">
  <h2>Tải video từ YouTube</h2>
  <form method="get" action="/download">
    <input name="url" type="text" placeholder="Dán link video..." style="width: 400px;" required /><br><br>
    <label>Chọn định dạng:</label>
    <select name="format">
      <option value="mp4">MP4 (video)</option>
      <option value="mp3">MP3 (âm thanh)</option>
    </select><br><br>
    <button type="submit">Tải về</button>
  </form>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download')
def download():
    video_url = request.args.get('url')
    fmt = request.args.get('format', 'mp4')

    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4().hex
    raw_output_path = os.path.join(temp_dir, f"video_{unique_id}")
    output_path = raw_output_path + f".{fmt}"

    if fmt == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': raw_output_path,
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
    elif fmt == "mp4":
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
        }
    else:
        return {"error": "Định dạng không được hỗ trợ"}, 400

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Nếu là mp3, tìm file .mp3 sinh ra thật
        if fmt == "mp3":
            mp3_path = None
            for f in os.listdir(temp_dir):
                if f.startswith(f"video_{unique_id}") and f.endswith(".mp3"):
                    mp3_path = os.path.join(temp_dir, f)
                    break
            if not mp3_path:
                raise Exception("Không tìm thấy file MP3 sau khi tải")
            output_path = mp3_path

        if not os.path.exists(output_path):
            raise Exception("File không tồn tại sau khi tải.")

        if fmt == "mp4" and not check_audio_in_video(output_path):
            raise Exception("Video không có âm thanh.")

        @after_this_request
        def cleanup(response):
            try:
                os.remove(output_path)
            except Exception as e:
                print(f"Lỗi khi xóa file: {e}")
            return response

        return send_file(
            output_path,
            as_attachment=True,
            download_name=os.path.basename(output_path),
            mimetype='application/octet-stream'
        )

    except Exception as e:
        return {"error": f"Tải video thất bại: {str(e)}"}, 500

def check_audio_in_video(file_path):
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return "Audio:" in result.stderr
    except Exception as e:
        print(f"Lỗi kiểm tra âm thanh: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True)
