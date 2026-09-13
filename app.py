from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)
CORS(app)

VOICES = {
    "female": "vi-VN-HoaiMyNeural",
    "male": "vi-VN-NamMinhNeural"
}

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": "Yezi Vietnamese TTS API"
    })

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}

    text = str(data.get("text", "")).strip()
    voice_key = data.get("voice", "female")

    if not text:
        return jsonify({"error": "請輸入文字"}), 400

    voice = VOICES.get(voice_key, VOICES["female"])

    temp = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )
    temp_path = temp.name
    temp.close()

    async def generate():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice
        )
        await communicate.save(temp_path)

    try:
        asyncio.run(generate())

        response = send_file(
            temp_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="speech.mp3"
        )

        @response.call_on_close
        def cleanup():
            try:
                os.remove(temp_path)
            except OSError:
                pass

        return response

    except Exception as e:
        try:
            os.remove(temp_path)
        except OSError:
            pass

        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
