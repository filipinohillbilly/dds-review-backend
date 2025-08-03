import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# === App Setup
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Health Check
@app.route("/", methods=["GET"])
def index():
    return "DDS backend server is live", 200

# === Upload Endpoint for Make.com
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        # Ensure file was sent
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]

        # Check that a filename exists
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Save file
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        print(f"✅ File received and saved to {save_path}")
        return jsonify({"message": "File uploaded successfully", "path": save_path}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

# === App Entry Point
if __name__ == "__main__":
    print("📡 Starting DDS backend server...")
    app.run(host="0.0.0.0", port=10000)
