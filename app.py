import os
import urllib.parse
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import time

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "YouTube Downloader API is running!"})

@app.route("/get_formats", methods=["POST"])
def get_formats():
    try:
        data = request.json
        video_url = data.get("url")

        if not video_url:
            return jsonify({"error": "No URL provided"}), 400

        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])

        available_formats = []
        for fmt in formats:
            if fmt.get('height'):  # Only consider video formats with height info
                available_formats.append({
                    "format_id": fmt['format_id'],
                    "height": fmt['height'],
                    "extension": fmt['ext'],
                    "format_note": fmt.get('format_note', '')
                })

        return jsonify({"formats": available_formats})

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/download", methods=["POST"])
def download_video():
    try:
        data = request.json
        video_url = data.get("url")
        selected_format = data.get("format")
        cookies = data.get("cookies")  # Directly accept cookies as part of the request

        if not video_url:
            return jsonify({"error": "No URL provided"}), 400
        if not selected_format:
            return jsonify({"error": "No format selected"}), 400

        # Ensure cookies are passed in the correct format
        if not cookies:
            return jsonify({"error": "Cookies are required for downloading"}), 400

        # Set yt-dlp options for the selected format
        ydl_opts = {
            "format": selected_format,
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            "cookiejar": None,  # No cookie file, we are passing cookies directly
            "cookies": cookies  # Pass cookies directly
        }

        start_time = time.time()  # Track start time

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_filename = f"{info['title']}.mp4"
            encoded_filename = urllib.parse.quote(video_filename)  # URL-encode the filename for safety

        end_time = time.time()  # Track end time
        time_taken = round(end_time - start_time, 2)

        return jsonify({
            "download_url": f"http://127.0.0.1:5000/download_file/{encoded_filename}",
            "time_taken": time_taken
        })

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/download_file/<filename>", methods=["GET"])
def download_file(filename):
    # Decode the filename to handle any special characters or spaces
    decoded_filename = urllib.parse.unquote(filename)
    file_path = os.path.join(DOWNLOAD_FOLDER, decoded_filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
