import os
import openai
import pdfplumber
from datetime import datetime

# === Load environment variables
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
INSTRUCTIONS_FILE = "GPT_Instructions.txt"
UPLOAD_FOLDER = "/tmp"

openai.api_key = OPENAI_API_KEY


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()


def load_instructions():
    with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
        return f.read()


def call_gpt_assistant(system_instructions, user_input):
    client = openai.OpenAI()
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        instructions=system_instructions
    )

    # Poll until complete
    while run.status not in ["completed", "failed", "cancelled"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    if run.status != "completed":
        raise Exception(f"❌ GPT Assistant run failed with status: {run.status}")

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value
    return response


def generate_pdf_from_text(content, output_path):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for line in content.split("\n"):
        pdf.multi_cell(0, 5, line)

    pdf.output(output_path)


def run_review():
    # 1. Load instructions
    instructions = load_instructions()

    # 2. Gather all 6 PDFs
    filenames = [f"{i}.pdf" for i in range(1, 7)]
    pdf_texts = []
    for filename in filenames:
        full_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(full_path):
            pdf_texts.append(extract_text_from_pdf(full_path))
        else:
            print(f"⚠️ Missing: {filename}")

    if len(pdf_texts) < 6:
        raise FileNotFoundError("❌ Not all expected PDFs found in upload folder.")

    combined_input = "\n\n".join(pdf_texts)

    # 3. Send to GPT Assistant
    print("📡 Sending data to GPT Assistant...")
    dds_output = call_gpt_assistant(instructions, combined_input)

    # 4. Create output PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_pdf_path = os.path.join(UPLOAD_FOLDER, f"DailyReport_{timestamp}.pdf")
    generate_pdf_from_text(dds_output, output_pdf_path)

    print(f"✅ DDS review saved to: {output_pdf_path}")
    return output_pdf_path


if __name__ == "__main__":
    run_review()
