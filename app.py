from flask import Flask, request, jsonify
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

app = Flask(__name__)

@app.route("/review", methods=["POST"])
def review():
    try:
        data = request.get_json()
        pdf_urls = data.get("pdf_links", [])
        run_id = data.get("run_id", "manual")

        if not pdf_urls:
            return jsonify({"error": "No PDF links provided"}), 400

        uploaded_files = []
        for url in pdf_urls:
            file = openai.files.create(file=url, purpose="assistants")
            uploaded_files.append(file.id)

        thread = openai.beta.threads.create()

        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Please run DDS review using the uploaded PDFs.",
            file_ids=uploaded_files
        )

        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({"error": "Run failed"}), 500

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        output = messages.data[0].content[0].text.value

        return jsonify({
            "run_id": run_id,
            "assistant_output": output
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
