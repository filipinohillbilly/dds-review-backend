import os
import logging
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from process import process_files
import werkzeug
import requests
from urllib.parse import urlparse, parse_qs

# === Constants
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
LOG_FILE = "server_errors.log"

# === Folder Creation
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Logging Setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === Flask App
app = Flask(__name__)
CORS(app)

# === Global State
latest_uploads = []
latest_output_filename = None
last_error = None

# === Root Route for sanity check
@app.route("/", methods=["GET"])
def root():
    logging.info("[ROOT] Health check endpoint called.")
    return "✅ DDS Review Backend is running.", 200

# === Optional: Health route
@app.route("/health", methods=["GET"])
def health():
    logging.info("[HEALTH] Health diagnostics requested.")
    return jsonify({
        "status": "online",
        "uploads": os.listdir(UPLOAD_FOLDER),
        "output": os.listdir(OUTPUT_FOLDER),
        "last_error": last_error or "None"
    }), 200

# === Updated Upload Endpoint for Make.com Module 17
@app.route("/upload", methods=["POST"])
def upload_files():
    global latest_uploads, last_error

    try:
        uploaded_file = request.files.get("file")
        if not uploaded_file:
            raise werkzeug.exceptions.BadRequest("No file provided in upload.")

        filename = uploaded_file.filename or "input.pdf"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        uploaded_file.save(save_path)
        logging.info(f"[UPLOAD] Received and saved: {filename}")

        latest_uploads = [filename]
        last_error = None
        return jsonify({"message": "Upload successful", "files": latest_uploads}), 200

    except Exception as e:
        last_error = f"[UPLOAD ERROR] {str(e)}"
        logging.error(last_error)
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 400

# === GET trigger for Module 18
@app.route("/process", methods=["GET"])
def process_files_route():
    global latest_output_filename, last_error

    try:
        filenames = os.listdir(UPLOAD_FOLDER)
        if not filenames:
            raise FileNotFoundError("No uploaded PDFs found in upload folder.")

        filepaths = [os.path.join(UPLOAD_FOLDER, name) for name in filenames]
        logging.info(f"[PROCESS] Starting processing of {len(filepaths)} files...")

        output_path, error = process_files(filepaths)

        if error:
            raise RuntimeError(error)

        latest_output_filename = os.path.basename(output_path)
        last_error = None
        logging.info(f"[SUCCESS] DDS review completed: {latest_output_filename}")
        return jsonify({"message": "Processing complete", "filename": latest_output_filename}), 200

    except Exception as e:
        last_error = f"[PROCESS ERROR] {str(e)}"
        logging.error(last_error)
        logging.error(traceback.format_exc())
        return jsonify({"error": last_error}), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        logging.error(f"[DOWNLOAD ERROR] File not found: {filename}")
        return jsonify({"error": "File not found"}), 404

@app.route("/status", methods=["GET"])
def status():
    try:
        with open(LOG_FILE, "r") as f:
            log_tail = f.readlines()[-10:]
    except Exception as e:
        log_tail = [f"Could not read log file: {str(e)}"]

    return jsonify({
        "latest_uploads": latest_uploads,
        "latest_output": latest_output_filename,
        "last_error": last_error or "None",
        "log_tail": log_tail
    }), 200

# === NEW: Google Drive link ingestion endpoint
@app.route("/process-gdrive", methods=["POST"])
def process_gdrive_links():
    global latest_output_filename, last_error

    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls or not isinstance(urls, list):
            raise ValueError("No valid list of URLs provided.")

        filepaths = []

        for url in urls:
            if "drive.google.com" not in url:
                continue

            file_id = None
            if "/file/d/" in url:
                file_id = url.split("/file/d/")[1].split("/")[0]
            elif "id=" in url:
                file_id = parse_qs(urlparse(url).query).get("id", [None])[0]

            if not file_id:
                raise ValueError(f"Invalid Google Drive URL: {url}")

            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = requests.get(download_url)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to download file from: {url}")

            filename = f"gdrive_{file_id}.pdf"
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(save_path, "wb") as f:
                f.write(response.content)

            logging.info(f"[GDRIVE] Downloaded and saved: {filename}")
            filepaths.append(save_path)

        output_path, error = process_files(filepaths)

        if error:
            raise RuntimeError(error)

        latest_output_filename = os.path.basename(output_path)
        last_error = None
        logging.info(f"[GDRIVE] DDS review completed: {latest_output_filename}")
        return jsonify({"message": "GDrive DDS complete", "filename": latest_output_filename}), 200

    except Exception as e:
        last_error = f"[GDRIVE ERROR] {str(e)}"
        logging.error(last_error)
        logging.error(traceback.format_exc())
        return jsonify({"error": last_error}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
