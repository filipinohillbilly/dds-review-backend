from flask import Flask, request, jsonify
import os
import fitz  # PyMuPDF
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "✅ DDS backend is online",
        "timestamp": "2025-08-04T00:15:00"
    })

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read PDF from uploaded file
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        if len(text.strip()) == 0:
            return jsonify({"error": "PDF appears to contain no text"}), 400

        # Call OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")

        prompt = f"""
You are a financial strategist. Read the following PDF contents and return a DDS (Defend / Destroy / Summarize) review of the portfolio:

{text}
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert portfolio analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )

        result = response.choices[0].message["content"]
        return jsonify({"analysis": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
