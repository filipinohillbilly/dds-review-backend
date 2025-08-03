from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key (from Render secret env var)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return jsonify({"message": "DDS review backend is live"}), 200

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # === Call OpenAI API to analyze content ===
        with open(file_path, "rb") as f:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a financial portfolio assistant. Perform a Defend / Destroy / Summarize (DDS) review of the uploaded portfolio snapshot."},
                    {"role": "user", "content": f"Please analyze this file: {file.filename}"},
                ],
                tools=[
                    {
                        "type": "file_search"
                    }
                ],
                tool_choice="auto",
                temperature=0.3
            )

        dds_result = response.choices[0].message.content
        return jsonify({"DDS_review": dds_result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
