from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import fitz  # PyMuPDF
import logging

app = Flask(__name__)

# === Health check route for Render ===
@app.route("/")
def home():
    return jsonify({
        "status": "✅ DDS backend is online",
        "timestamp": "2025-08-04T00:15:00"
    })

# === Upload endpoint ===
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        file.save(tmp_file.name)

        try:
            # Extract text with PyMuPDF
            doc = fitz.open(tmp_file.name)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            return jsonify({
                "filename": filename,
                "text": full_text.strip()
            })

        except Exception as e:
            logging.exception("PDF processing failed.")
            return jsonify({"error": str(e)}), 500
        finally:
            os.remove(tmp_file.name)

# === Main entry point ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
