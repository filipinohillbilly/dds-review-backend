import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

# === Load env vars
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# === Validate
if not OPENAI_API_KEY:
    raise RuntimeError("❌ Missing OPENAI_API_KEY in environment variables.")
if not ASSISTANT_ID:
    raise RuntimeError("❌ Missing ASSISTANT_ID in environment variables.")

# === Init API + Flask
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ DDS Assistant Backend is Live"

@app.route("/submit", methods=["POST"])
def handle_submit():
    try:
        data = request.get_json()
        file_id = data.get("file_id")

        if not file_id:
            return jsonify({"error": "Missing file_id in request."}), 400

        print(f"📎 Received file_id: {file_id}")

        run = openai.beta.threads.create_and_run(
            assistant_id=ASSISTANT_ID,
            thread={
                "messages": [
                    {
                        "role": "user",
                        "content": "Perform a DDS portfolio review based on the attached file.",
                        "file_ids": [file_id]
                    }
                ]
            }
        )

        print(f"🚀 OpenAI Run ID: {run.id}")
        return jsonify({"run_id": run.id, "status": run.status}), 200

    except Exception as e:
        print(f"❌ Error during /submit: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/status/<run_id>", methods=["GET"])
def check_status(run_id):
    try:
        run = openai.beta.threads.runs.retrieve(run_id=run_id)
        return jsonify({
            "status": run.status,
            "completed_at": run.completed_at,
            "required_action": run.required_action
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Required for Render deployment
if __name__ == "__main__":
    print("📡 Starting DDS backend server...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
