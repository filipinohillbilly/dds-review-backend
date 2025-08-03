import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# === Init Flask
app = Flask(__name__)
CORS(app)

# === OpenAI Auth
openai.api_key = os.getenv("OPENAI_API_KEY")  # Must be set in environment variables
ASSISTANT_ID = "asst_xxxxxxxxxxxxxxxxx"       # 🔁 Replace with your real Assistant ID

@app.route("/")
def index():
    return "DDS Assistant Backend is Live"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        files = request.files.getlist("files")
        if not files or files[0].filename == "":
            return jsonify(error="No files received in 'files' field."), 400

        # Step 1: Upload files to OpenAI
        uploaded_files = []
        for f in files:
            file_upload = openai.files.create(
                file=f,
                purpose="assistants"
            )
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

        # Step 5: Poll for completion
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status in ["cancelled", "failed", "expired"]:
                return jsonify(error=f"Run status: {run_status.status}"), 500
            time.sleep(2)

        # Step 6: Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread.id)

        output = []
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if content.type == "text":
                        output.append(content.text.value)

        if not output:
            return jsonify(message="No assistant response found."), 200

        return jsonify(response="\n\n".join(output)), 200

    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
