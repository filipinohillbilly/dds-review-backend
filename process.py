
import os
import fitz  # PyMuPDF
import openai
from datetime import datetime
from fpdf import FPDF

# === Load API Key and Constants
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")  # Optional fallback
UPLOAD_FOLDER = "/tmp"
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "GPT_Instructions.txt")

# === Global Tracker for /process Endpoint
latest_output_filename = ""  # Will be updated after each run

# === Utility: Extract text from PDFs
def extract_text_from_pdf(filepath):
    try:
        with fitz.open(filepath) as doc:
            return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        return f"[ERROR extracting text from {filepath}: {str(e)}]"

# === Utility: Load DDS instruction prompt
def load_instructions():
    try:
        with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return "[ERROR: Could not load instructions]"

# === Utility: Generate GPT DDS Review
def get_gpt_review(instructions, content):
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": content}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.4,
        max_tokens=3000
    )

    return response['choices'][0]['message']['content']

# === Utility: Save DDS result to PDF
def save_to_pdf(text, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10)

    for line in text.splitlines():
        pdf.multi_cell(0, 5, line)

    output_path = os.path.join(UPLOAD_FOLDER, filename)
    pdf.output(output_path)
    return output_path

# === Core DDS Processor Entry Point
def process_files(filepaths):
    global latest_output_filename  # <-- Required for /process route

    try:
        combined_text = ""
        for path in filepaths:
            combined_text += f"\n\n===== {os.path.basename(path)} =====\n"
            combined_text += extract_text_from_pdf(path)

        instructions = load_instructions()
        dds_output = get_gpt_review(instructions, combined_text)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        final_filename = f"DDS_Review_{timestamp}.pdf"
        final_path = save_to_pdf(dds_output, final_filename)

        latest_output_filename = final_filename  # <-- Required for status endpoint
        return final_path

    except Exception as e:
        return f"[PROCESSING ERROR: {str(e)}]"
