import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import subprocess
import time

# === App Setup
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"
REQUIRED_FILENAMES = [f"{i}.pdf" for i in range(1, 7)]
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Health Check
@app.route("/", methods=["GET"])
def index():
    return "DDS backend server is live", 200

# === Upload Endpoint
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        print(f"✅ File received and saved to {save_path}")

        # === Check if all 6 required PDFs are now present
        uploaded_files = os.listdir(UPLOAD_FOLDER)
        if all(name in uploaded_files for name in REQUIRED_FILENAMES):
            print("📦 All 6 files received. Running process.py...")

            # === Run process.py
            result = subprocess.run(["python3", "process.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(result.stderr)
                return jsonify({"error": "DDS report generation failed", "details": result.stderr}), 500

            # === Get most recent DailyReport_*.pdf file
            files = [f for f in os.listdir(UPLOAD_FOLDER) if f.startswith("DailyReport_") and f.endswith(".pdf")]
            if not files:
                return jsonify({"error": "No DDS report file found"}), 500
            files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)), reverse=True)
            report_path = os.path.join(UPLOAD_FOLDER, files[0])
            print(f"📄 DDS report generated at {report_path}")

            return jsonify({
                "message": "All files received. DDS report generated.",
                "report_path": report_path
            }), 200

        else:
            remaining = [f for f in REQUIRED_FILENAMES if f not in uploaded_files]
            return jsonify({
                "message": "File received, waiting on remaining files.",
                "remaining": remaining
            }), 202

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

# === App Entry Point
if __name__ == "__main__":
    print("📡 Starting DDS backend server...")
    app.run(host="0.0.0.0", port=10000)
