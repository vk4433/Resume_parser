import os
import re
import docx
import spacy
import fitz
import logging
import win32com.client as win32
import phonenumbers
from spacy.matcher import Matcher
nlp = spacy.load('en_core_web_sm')
matcher = Matcher(nlp.vocab)

class ResumeParse:
    objective_keywords = (
        "career goal", "objective", "career objective", "employment objective",
        "professional objective", "career summary", "professional summary",
        "summary of qualifications", "summary", "PROFESSIONAL SUMMARY",
        "SUMMARY", "Professional Summary", "profile", "About Me"
    )

    def extract_text_docx(self, docx_file):
        try:
            doc = docx.Document(docx_file)
            text = '\n'.join([para.text for para in doc.paragraphs])
            clean_text = re.sub(r'\n+', '\n', text)
            clean_text = clean_text.replace("\r", "\n").replace("\t", " ")
            resume_lines = clean_text.splitlines()
            resume_lines = [re.sub(r'\s+', ' ', line.strip()) for line in resume_lines if line.strip()]
            return resume_lines, text
        except Exception as e:
            logging.error(f'Error processing DOCX file {docx_file}: {e}')
            return [], ""

    def extract_text_pdf(self, pdf_file):
        try:
            with fitz.open(pdf_file) as pdf:
                text = "".join(page.get_text() for page in pdf)
            clean_text = re.sub(r'\n+', '\n', text)
            clean_text = clean_text.replace("\r", "\n").replace("\t", " ")
            resume_lines = clean_text.splitlines()
            resume_lines = [re.sub(r'\s+', ' ', line.strip()) for line in resume_lines if line.strip()]
            return resume_lines, text
        except Exception as e:
            logging.error(f'Error processing PDF file {pdf_file}: {e}')
            return [], ""

    def extract_text_doc(self, doc_file):
        try:
            word = win32.Dispatch("Word.Application")
            doc = word.Documents.Open(doc_file)
            text = doc.Content.Text
            doc.Close()
            word.Quit()
            clean_text = re.sub(r'\n+', '\n', text)
            clean_text = clean_text.replace("\r", "\n").replace("\t", " ")
            resume_lines = clean_text.splitlines()
            resume_lines = [re.sub(r'\s+', ' ', line.strip()) for line in resume_lines if line.strip()]
            return resume_lines, text
        except Exception as e:
            logging.error(f'Error processing DOC file {doc_file}: {e}')
            return [], ""

    def read_file(self, file):
        file = os.path.abspath(file)
        if file.endswith('.docx'):
            return self.extract_text_docx(file)
        elif file.endswith('.pdf'):
            return self.extract_text_pdf(file)
        elif file.endswith('.doc'):
            return self.extract_text_doc(file)
        elif file.endswith('.txt'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    resume_lines = f.readlines()
                    raw_text = ''.join(resume_lines)
                return resume_lines, raw_text
            except Exception as e:
                logging.error(f'Error reading TXT file {file}: {e}')
                return [], ""
        else:
            logging.error(f"Unsupported file format: {file}")
            return [], ""

    def professional_summery(self, resume_lines):
        capturing = False
        professional_summary_section = []
        section_started = False

        for line in resume_lines:
            if any(re.search(r'\b' + re.escape(header) + r'\b', line, re.IGNORECASE) for header in self.objective_keywords):
                capturing = True
                section_started = True
                continue
            elif capturing:
                if len(re.findall(r'[A-Z]', line)) / len(line) >= 0.5 or len(line) >=30:
                    capturing = False
                    break
                professional_summary_section.append(line)

        if not section_started:
            return {"professional_summary": []}

        return {"professional_summary": professional_summary_section}

if __name__ == "__main__":
    parser = ResumeParse()
    file_path = 'Narendra.pdf'  
    resume_lines, full_text = parser.read_file(file_path)
   
    resume_segments = parser.professional_summery(resume_lines)

    professional_summary_section = resume_segments.get("professional_summary", [])
    if not professional_summary_section:
        print("  None")
    else:
        print("Professional Summary")
        for line in professional_summary_section:
            print(f"  {line}")
