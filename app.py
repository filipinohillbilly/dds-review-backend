import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from process import process_files, latest_output_filename  # DDS logic + output tracking

# === App Setup
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Health Check
@app.route("/", methods=["GET"])
def index():
    return "DDS backend server is live", 200

# === Upload Endpoint (Make.com POSTs PDF here)
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

        # === Run DDS Logic
        generated_path = process_files([save_path])
        print(f"📄 DDS PDF saved to {generated_path}")

        return jsonify({
            "message": "File uploaded and processed successfully",
            "report_pdf": generated_path,
            "download_url": f"https://dds-review-backend.onrender.com/download/{os.path.basename(generated_path)}"
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

# === PDF Download Route
@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": f"File '{filename}' not found"}), 404

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

# === GET Process Status
@app.route("/process", methods=["GET"])
def process_file():
    try:
        output_path = os.path.join(UPLOAD_FOLDER, latest_output_filename)
        if os.path.exists(output_path):
            return jsonify({
                "output_file": latest_output_filename,
                "url": f"https://dds-review-backend.onrender.com/download/{latest_output_filename}"
            }), 200
        else:
            return jsonify({"error": "Latest output file not found."}), 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Process check failed: {str(e)}"}), 500

# === Entry Point
if __name__ == "__main__":
    print("📡 Starting DDS backend server...")
    app.run(host="0.0.0.0", port=10000)
