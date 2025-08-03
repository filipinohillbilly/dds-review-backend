from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Optional: allow CORS if Make or browser will hit this

@app.route('/')
def index():
    return jsonify({"message": "DDS review backend is live"}), 200

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Check if the request contains a file part
        if 'file' not in request.files:
            print("❌ No file part in the request")
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']

        # Check if a filename exists
        if file.filename == '':
            print("❌ No selected file")
            return jsonify({"error": "No file selected"}), 400

        # Save file temporarily or handle in-memory
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        print(f"✅ File '{file.filename}' received and saved to {file_path}")
        return jsonify({"message": f"File '{file.filename}' received successfully"}), 200

    except Exception as e:
        print(f"💥 Exception during file upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

