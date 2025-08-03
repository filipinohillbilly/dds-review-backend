import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# === Init Flask
app = Flask(__name__)
CORS(app)

# === OpenAI Auth
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")  # Load from Render environment variable

@app.route("/")
def index():
    return "DDS Assistant Backend is Live"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "files" not in request.files:
            return jsonify(error="No files uploaded."), 400

        files = request.files.getlist("files")
        if not files:
            return jsonify(error="Empty file list."), 400

        # Step 1: Upload all files to OpenAI
        uploaded_file_ids = []
        for f in files:
            upload = openai.files.create(file=f, purpose="assistants")
            uploaded_file_ids.append(upload.id)

        # Step 2: Create a new thread
        thread = openai.beta.threads.create()

        # Step 3: Send a message with file references
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Please perform a full DDS (Defend / Destroy / Summarize) analysis of these PDFs.",
            file_ids=uploaded_file_ids
        )

        # Step 4: Run the assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        return jsonify(message="Files uploaded and assistant triggered.", run_id=run.id, thread_id=thread.id)

    except Exception as e:
        return jsonify(error=str(e)), 500
