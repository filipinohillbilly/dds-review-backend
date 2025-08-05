import os
import fitz  # PyMuPDF
import openai
import traceback
from datetime import datetime
from fpdf import FPDF
import logging

# === Constants
OUTPUT_FOLDER = "output"
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "GPT_Instructions.txt")
LOG_FILE = "server_errors.log"

# === Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === Load OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.warning("[INIT] OPENAI_API_KEY not found in environment.")

# === Utility: Extract text from a PDF
def extract_text_from_pdf(filepath):
    try:
        with fitz.open(filepath) as doc:
            text = "\n".join([page.get_text().strip() for page in doc])
            if not text.strip():
                raise ValueError(f"Empty text extracted from {filepath}")
            logging.info(f"[EXTRACT] Extracted from {os.path.basename(filepath)} — {len(text)} chars")
            return text
    except Exception as e:
        logging.error(f"[EXTRACT ERROR] {filepath}")
        logging.error(traceback.format_exc())
        raise RuntimeError(f"Text extraction failed for {filepath}: {str(e)}")

# === Utility: Load GPT instructions
def load_instructions():
    try:
        if not os.path.exists(INSTRUCTIONS_FILE):
            raise FileNotFoundError("GPT_Instructions.txt not found.")

        with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
            instructions = f.read().strip()
            if not instructions:
                raise ValueError("Instruction file is empty.")
            logging.info("[LOAD] GPT instructions loaded successfully.")
            return instructions
    except Exception as e:
        logging.error("[LOAD ERROR] Failed to load GPT instructions")
        logging.error(traceback.format_exc())
        raise

# === Utility: Get GPT DDS output
def get_gpt_review(instructions, content):
    try:
        logging.info(f"[GPT] Sending {len(content.split())} tokens to GPT...")

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

        result = response['choices'][0]['message']['content']
        logging.info(f"[GPT] Received DDS review — {len(result)} chars")
        return result

    except Exception as e:
        logging.error("[GPT ERROR] GPT DDS generation failed")
        logging.error(traceback.format_exc())
        raise RuntimeError(f"GPT DDS generation failed: {str(e)}")

# === Utility: Save result to PDF
def save_to_pdf(text, filename):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Courier", size=10)

        for line in text.splitlines():
            pdf.multi_cell(0, 5, line)

        output_path = os.path.join(OUTPUT_FOLDER, filename)
        pdf.output(output_path)
        logging.info(f"[SAVE] DDS PDF created at {output_path}")
        return output_path

    except Exception as e:
        logging.error("[SAVE ERROR] Failed to generate output PDF")
        logging.error(traceback.format_exc())
        raise RuntimeError(f"Failed to save DDS output as PDF: {str(e)}")

# === Core Processor Entry Point
def process_files(filepaths):
    try:
        combined_text = ""

        for path in filepaths:
            extracted = extract_text_from_pdf(path)
            combined_text += f"\n\n===== {os.path.basename(path)} =====\n{extracted}"

        instructions = load_instructions()
        dds_output = get_gpt_review(instructions, combined_text)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"DDS_Review_{timestamp}.pdf"
        final_path = save_to_pdf(dds_output, filename)

        return final_path, None

    except Exception as e:
        logging.error("[PROCESS ERROR] DDS pipeline failed")
        logging.error(traceback.format_exc())
        return None, str(e)
