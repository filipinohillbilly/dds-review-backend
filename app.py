import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# === Init Flask
app = Flask(__name__)
CORS(app)

# === OpenAI Auth
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = "asst_xxxxxxxxxxxxx"  # 🔁 Replace with your real assistant ID

@app.route("/")
def index():
    return "DDS Assistant Backend is Live"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "files" not in request.files:
            return jsonify(error="No file(s) uploaded."), 400

        files = request.files.getlist("files")
        if not files:
            return jsonify(error="Empty file list."), 400

        # Step 1: Upload files to OpenAI
        uploaded_files = []
        for f in files:
            file_upload = openai.files.create(file=f, purpose="assistants")
            uploaded_files.append(file_upload.id)

        # Step 2: Create a thread
        thread = openai.beta.threads.create()

        # Step 3: Send a message with file references
        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Please perform a full DDS (Defend / Destroy / Summarize) analysis of this PDF.",
            file_ids=uploaded_files
        )

        # Step 4: Run the assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Step 5: Poll for run completion
        print("⏳ Waiting for run to complete...")
        while True:
            run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status == "failed":
                return jsonify(error="DDS run failed."), 500
            time.sleep(2)

        # Step 6: Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return jsonify(message=msg.content[0].text.value), 200

        return jsonify(message="DDS run completed but no assistant response found."), 200

    except Exception as e:
        print("❌ Error:", e)
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
