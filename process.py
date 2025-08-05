import os
import fitz  # PyMuPDF
import openai
from datetime import datetime
from fpdf import FPDF

# === Load API Key and Constants
openai.api_key = os.getenv("OPENAI_API_KEY")
UPLOAD_FOLDER = "/tmp"
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "GPT_Instructions.txt")

# === Utility: Extract text from PDF
def extract_text_from_pdf(filepath):
    try:
        with fitz.open(filepath) as doc:
            return "\n".join([page.get_text().strip() for page in doc])
    except Exception as e:
        return f"[ERROR extracting text from {filepath}: {str(e)}]"

# === Utility: Load DDS prompt instructions
def load_instructions():
    try:
        with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return "[ERROR: Could not load GPT instructions file.]"

# === Utility: Run GPT DDS Review
def get_gpt_review(instructions, content):
    try:
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

    except Exception as e:
        return f"[GPT ERROR: Failed to generate review. {str(e)}]"

# === Utility: Save text to PDF
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

# === Core Processor Entry Point
def process_files(filepaths):
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

        return final_path

    except Exception as e:
        return f"[PROCESSING ERROR: {str(e)}]"
