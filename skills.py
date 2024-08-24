import os
import re
import logging
import docx2txt
import pdfplumber
import spacy
from spacy.matcher import Matcher
import phonenumbers
from spacy.matcher import PhraseMatcher
base_path = os.path.dirname(__file__)

# Load the spaCy language model
nlp = spacy.load('en_core_web_sm')
matcher = Matcher(nlp.vocab)

file = os.path.join(base_path,"LINKEDIN_SKILLS_ORIGINAL.txt")
file = open(file, "r", encoding='utf-8')    
skill = [line.strip().lower() for line in file]
skillsmatcher = PhraseMatcher(nlp.vocab)
patterns = [nlp.make_doc(text) for text in skill if len(nlp.make_doc(text)) < 10]
skillsmatcher.add("Job title", None, *patterns)

def extract_text_docx(docx_file):
        text = docx2txt.process(docx_file)
        clean_text = re.sub(r'\n+', '\n', text)
        clean_text = clean_text.replace("\r", "\n").replace("\t", " ")
        resume_lines = clean_text.splitlines()
        resume_lines = [re.sub(r'\s+', ' ', line.strip()) for line in resume_lines if line.strip()]
        return resume_lines, text
    

def extract_text_pdf(pdf_file):
        with pdfplumber.open(pdf_file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
        clean_text = re.sub(r'\n+', '\n', text)
        clean_text = clean_text.replace("\r", "\n").replace("\t", " ")
        resume_lines = clean_text.splitlines()
        resume_lines = [re.sub(r'\s+', ' ', line.strip()) for line in resume_lines if line.strip()]
        return resume_lines, text
     

def read_file(file):
    file = os.path.abspath(file)
    if file.endswith('docx') or file.endswith('doc'):
        return extract_text_docx(file)
    elif file.endswith('pdf'):
        return extract_text_pdf(file)
    elif file.endswith('txt'):
        with open(file, 'r', encoding='latin') as f:
            resume_lines = f.readlines()
            raw_text = ''.join(resume_lines)
        return resume_lines, raw_text
    else:
        logging.error("Unsupported file format")
        return [], ""
    
def extract_skills(text):
        skills = []

        __nlp = nlp(text.lower())
        # Only run nlp.make_doc to speed things up

        matches = skillsmatcher(__nlp)
        for match_id, start, end in matches:
            span = __nlp[start:end]
            skills.append(span.text)
        skills = list(set(skills))
        return set(skills)

 



if __name__ == "__main__":
    file_path = 'preethi.pdf'
    resume_lines, full_text = read_file(file_path)


skills = extract_skills(full_text)
print("skills:",skills)