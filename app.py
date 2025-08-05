import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from process import process_files  # ✅ Centralized logic
import werkzeug

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)

# === Global state for diagnostics
latest_uploads = []
latest_output_filename = None
last_error = None

@app.route("/upload", methods=["POST"])
def upload_files():
    global latest_uploads, last_error

    try:
        uploaded_files = request.files.getlist("files")
        if not uploaded_files:
            raise werkzeug.exceptions.BadRequest("No files provided in upload.")

        filepaths = []
        for file in uploaded_files:
            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)
            filepaths.append(save_path)
            print(f"[UPLOAD] Received and saved: {filename}")

        latest_uploads = [os.path.basename(f) for f in filepaths]
        last_error = None
        return jsonify({"message": "Upload successful", "files": latest_uploads}), 200

    except Exception as e:
        last_error = f"[UPLOAD ERROR] {str(e)}"
        print(last_error)
        return jsonify({"error": str(e)}), 400

@app.route("/process", methods=["GET"])
def process_files_route():
    global latest_output_filename, last_error

    try:
        filenames = os.listdir(UPLOAD_FOLDER)
        if not filenames:
            raise FileNotFoundError("No uploaded PDFs found in upload folder.")

        filepaths = [os.path.join(UPLOAD_FOLDER, name) for name in filenames]
        print(f"[PROCESS] Starting processing of {len(filepaths)} files...")

        output_path, error = process_files(filepaths)

        if error:
            raise RuntimeError(error)

        latest_output_filename = os.path.basename(output_path)
        last_error = None
        print(f"[SUCCESS] DDS review completed: {latest_output_filename}")
        return jsonify({"message": "Processing complete", "filename": latest_output_filename}), 200

    except Exception as e:
        last_error = f"[PROCESS ERROR] {str(e)}"
        print(last_error)
        return jsonify({"error": last_error}), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "latest_uploads": latest_uploads,
        "latest_output": latest_output_filename,
        "last_error": last_error or "None"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
