from flask import Flask, render_template, request
import pdfplumber
import google.generativeai as genai
import os
from dotenv import load_dotenv  # To load environment variables from the .env file

# 📦 Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set the folder path for uploaded resumes
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Ensure the 'uploads' folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 🔑 Configure Gemini API Key securely from environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-pro")

# 📄 PDF Text Extractor
def extract_text_from_pdf(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    return text.strip()

# 🔍 Resume Analysis for Candidate
def analyze_resume_for_candidate(text):
    prompt = f"""
    Analyze this resume and provide:
    - A brief summary of the candidate
    - Key skills and technologies
    - Suggestions for improvement
    - Recommended job roles or industries

    Resume:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

# 🔍 Resume Analysis for HR
def analyze_resume_for_hr(text):
    prompt = f"""
    Analyze this resume and provide the key points for an HR professional in just 5 lines. Focus on:
    - Key skills and technologies (keywords, short list)
    - Education details (1 line summary)
    - Red flags (if any, in 1 line)

    Resume:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

# 🌐 Main Route
@app.route('/', methods=['GET', 'POST'])
def index():
    analysis_result = None
    if request.method == 'POST':
        role = request.form.get('role')
        uploaded_file = request.files['resume']

        if uploaded_file and uploaded_file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(file_path)

            resume_text = extract_text_from_pdf(file_path)

            if role == 'candidate':
                analysis_result = analyze_resume_for_candidate(resume_text)
            elif role == 'hr':
                analysis_result = analyze_resume_for_hr(resume_text)
            else:
                analysis_result = "Invalid role selected."

    return render_template('index.html', result=analysis_result)

# 🚀 Run the app (compatible with Replit or Render)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
