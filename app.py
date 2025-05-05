from flask import Flask, render_template, request
import pdfplumber
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])  # Create 'uploads' folder if it doesn't exist

# Configure Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables.")

print(f"🔑 GEMINI_API_KEY: {api_key[:5]}...")  # Print part of the key for debugging (remove in production)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-1.5-pro")

# Function to sanitize the uploaded filename (replace special characters with underscores)
def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

# Extract text from PDF
def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
        return text.strip()
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {str(e)}")
        return f"Error extracting text from PDF: {str(e)}"

# Candidate analysis
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
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ Error during candidate analysis: {str(e)}")
        return f"⚠️ Error during analysis: {str(e)}"

# HR analysis
def analyze_resume_for_hr(text):
    prompt = f"""
    Analyze this resume and provide the key points for an HR professional in just 5 lines. Focus on:
    - Key skills and technologies (keywords, short list)
    - Education details (1 line summary)
    - Red flags (if any, in 1 line)

    Resume:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ Error during HR analysis: {str(e)}")
        return f"⚠️ Error during analysis: {str(e)}"

# Main route
@app.route('/', methods=['GET', 'POST'])
def index():
    analysis_result = None

    if request.method == 'POST':
        try:
            role = request.form.get('role')
            uploaded_file = request.files.get('resume')

            if uploaded_file and uploaded_file.filename.endswith('.pdf'):
                # Sanitize the filename before saving
                sanitized_filename = sanitize_filename(uploaded_file.filename)

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)
                uploaded_file.save(file_path)

                print(f"✅ Uploaded file: {sanitized_filename}")
                resume_text = extract_text_from_pdf(file_path)
                print(f"📄 Extracted text preview: {resume_text[:300]}")  # Print first 300 chars of extracted text

                if "Error" in resume_text:
                    analysis_result = resume_text
                elif role == 'candidate':
                    analysis_result = analyze_resume_for_candidate(resume_text)
                elif role == 'hr':
                    analysis_result = analyze_resume_for_hr(resume_text)
                else:
                    analysis_result = "⚠️ Invalid role selected."
            else:
                analysis_result = "⚠️ Please upload a valid PDF file."

        except Exception as e:
            print(f"❌ Exception during processing: {str(e)}")
            analysis_result = f"❌ Internal error occurred: {str(e)}"

    return render_template('index.html', result=analysis_result)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)  # Running with debug mode enabled locally
