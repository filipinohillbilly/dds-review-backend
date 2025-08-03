from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"message": "DDS review backend is live"}), 200

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            print("❌ No file part in the request")
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        if file.filename == '':
            print("❌ No selected file")
            return jsonify({"error": "No file selected"}), 400

        # Save the file temporarily
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)
        print(f"✅ File '{file.filename}' received and saved to {file_path}")

        # === Place your analysis logic here ===
        # For now, we just pretend we processed it
        print("📊 DDS analysis placeholder triggered...")

        return jsonify({
            "message": f"File '{file.filename}' received successfully",
            "status": "success",
            "path": file_path
        }), 200

    except Exception as e:
        print(f"❌ Exception during file upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
