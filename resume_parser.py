import os
import re
import docx
import spacy
import fitz
import logging
import phonenumbers
from spacy.matcher import Matcher, PhraseMatcher

base_path = os.path.dirname(__file__)

nlp = spacy.load('en_core_web_sm')
nlp_t = spacy.load('en_core_web_trf')
matcher = Matcher(nlp.vocab)

class ResumeParse:
    RESERVED_WORDS = (
        'school', 'college', 'university', 'academy', 'faculty', 'institute',
        'faculdades', 'Schola', 'schule', 'lise', 'lyceum', 'lycee',
        'polytechnic', 'kolej', 'ünivers', 'okul', 'bachelor', 'masters',
        'bachelors', 'nit'
    )

    file_path = os.path.join(base_path, "LINKEDIN_SKILLS_ORIGINAL.txt")
    with open(file_path, "r", encoding='utf-8') as file:
        skills = [line.strip().lower() for line in file]

    def __init__(self):
        self.skillsmatcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(text) for text in ResumeParse.skills]
        self.skillsmatcher.add("SKILLS", None, *patterns)

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

    def read_file(self, file):
        file = os.path.abspath(file)
        if file.endswith('.docx'):
            return self.extract_text_docx(file)
        elif file.endswith('.pdf'):
            return self.extract_text_pdf(file)
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

    def extract_name(self, full_text):
        pattern1 = [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]
        pattern2 = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]

        matcher.add('NAME_PATTERN1', [pattern1])
        matcher.add('NAME_PATTERN2', [pattern2])

        for line in full_text:
            doc = nlp(line)
            matches = matcher(doc)

            match_found = None

            for match_id, start, end in matches:
                pattern_name = nlp.vocab.strings[match_id]
                span = doc[start:end]

                if pattern_name == 'NAME_PATTERN1':
                    match_found = span
                    break
                elif pattern_name == 'NAME_PATTERN2':
                    match_found = span

            if match_found:
                return match_found.text
        return None

    def find_email(self, full_text):
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        return re.findall(email_pattern, full_text, re.IGNORECASE)

    def find_phone(self, text):
        try:
            phone_numbers = list(phonenumbers.PhoneNumberMatcher(text, None))
            if phone_numbers:
                return phone_numbers[0].raw_string
        except Exception as e:
            pass

        try:
            match = re.search(r'\+?\d[\d\s\-\(\)\.]{7,}\d', text)
            if match:
                return match.group()
        except Exception as e:
            pass

        return ""

    def extract_companies(self, text):
        doc = nlp_t(text)
        companies = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        return set(companies)

    def extract_education(self, input_text):
        doc = nlp_t(input_text)
        college = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        education = set()
        for clg in college:
            for word in ResumeParse.RESERVED_WORDS:
                if word.lower() in clg.lower():
                    education.add(clg)
        return education

    def filter_company(self, education, companies):
        return {comp for comp in companies if comp not in education}

    def filter_companies_by_skills(self, companies):
        filtered_companies = set()
        for company in companies:
            doc = nlp(company.lower())
            matches = self.skillsmatcher(doc)
            if not any([match for match in matches]):
                filtered_companies.add(company)
        return filtered_companies


if __name__ == "__main__":
    parser = ResumeParse()
    file_path = 'resume.pdf'
    resume_lines, full_text = parser.read_file(file_path)

    candidate_name = parser.extract_name(resume_lines)
    print('Extracted Name:', candidate_name)

    email = parser.find_email(full_text)
    print("Extracted Email:", email)

    phone = parser.find_phone(full_text)
    print("Extracted Phone Number:", phone)

    companies = parser.extract_companies(full_text)

    education_information = parser.extract_education(full_text)
    print("education_information:", education_information)

    company = parser.filter_company(education_information, companies)

    filtered_companies_by_skills = parser.filter_companies_by_skills(company)
    print("organizations in resume:", filtered_companies_by_skills)
