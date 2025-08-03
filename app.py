import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# === Flask Setup
app = Flask(__name__)
CORS(app)

# === OpenAI Setup
openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure this is set in Render environment

# === Your Assistant ID
ASSISTANT_ID = "asst_XXXXXXXXXXXX"  # Replace with your actual Assistant ID

@app.route("/", methods=["GET"])
def home():
    return "DDS Assistant Backend is live."

@app.route("/upload", methods=["POST"])
def upload_pdf():
    try:
        file = request.files["file"]
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        # Step 1: Upload file to OpenAI
        uploaded_file = openai.files.create(
            file=file,
            purpose="assistants"
        )

        # Step 2: Create a new thread
        thread = openai.beta.threads.create()

        # Step 3: Add a message referencing the file
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Please perform a full DDS (Defend / Destroy / Summarize) analysis of this PDF.",
            file_ids=[uploaded_file.id]
        )

        # Step 4: Run the assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Step 5: Poll for run completion
        print("⏳ Waiting for DDS run to complete...")
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                raise Exception("❌ GPT DDS run failed.")
            time.sleep(3)

        # Step 6: Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread.id)

        # Step 7: Extract latest assistant message
        for msg in messages.data:
            if msg.role == "assistant":
                print("\n📘 DDS Assistant Response:\n")
                print(msg.content[0].text.value)
                return jsonify({"message": msg.content[0].text.value}), 200

        return jsonify({"message": "No assistant response found."}), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
