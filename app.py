from flask import Flask, request, jsonify
import openai
import os
from datetime import datetime
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

# === Initialize Flask app ===
app = Flask(__name__)

# === Root endpoint ===
@app.route("/", methods=["GET"])
def root():
    return {
        "status": "✅ DDS backend is online",
        "timestamp": datetime.now().isoformat()
    }

# === Review endpoint ===
@app.route("/review", methods=["POST"])
def review():
    try:
        data = request.get_json()
        pdf_urls = data.get("pdf_links", [])
        run_id = data.get("run_id", "manual")

        if not pdf_urls:
            return jsonify({"error": "No PDF links provided"}), 400

        # Placeholder for future logic
        return jsonify({
            "message": "PDF review initiated",
            "pdf_count": len(pdf_urls),
            "run_id": run_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Run locally if needed (commented out for deployment) ===
# if __name__ == "__main__":
#     app.run(debug=True)

