import os
import json
import logging
import re
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, flash
import google.generativeai as genai
from dotenv import load_dotenv
import markdown2
import pdfkit
from models import db, PersonalInfo, Experience, Education, JobApplication, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm
import click
from werkzeug.utils import secure_filename
from utils.cv_style import cv_styles
from utils.generic_style import generic_styles
from PyPDF2 import PdfMerger
from functools import wraps
import openai

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY
OPENAI_MODEL = os.getenv('CHATGPT_MODEL', 'gpt-4o-mini')


# Configure API key
API_KEY = os.getenv('API_KEY', 'your-default-api-key-here')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 檢查是否已經通過 web 登錄
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # 如果沒有登錄，檢查 API key
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
            
        # 如果既沒有登錄也沒有有效的 API key
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    return decorated_function

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")
genai.configure(api_key=GOOGLE_API_KEY)
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
model = genai.GenerativeModel(GEMINI_MODEL)

# Configure PDFKit
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
# Setup logging
logging.basicConfig(level=logging.INFO)

# Use instance_relative_config to let Flask know the instance folder exists
app = Flask(__name__, instance_relative_config=True)

# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'cv_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-secret-key-you-should-change')

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def setup_database():
    # This function now assumes it's called within an app context
    db.create_all()
    
    # Check if a user needs to be created
    if not User.query.first():
        # Create a default user for initial login
        default_user = User(username='admin')
        default_user.set_password('Love2025')
        db.session.add(default_user)
        
    # Check if CV JSON exists and DB is empty for personal info
    if os.path.exists('cv.json') and not PersonalInfo.query.first():
        with open('cv.json', 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
            
            # Consolidate personal info data from cv.json
            pi_data = cv_data.get('personal_info', {})
            root_keys = [
                'design_philosophy', 'skills', 'professional_attributes',
                'awards_and_recognitions', 'publications', 'references',
                'possible_titles', 'cover_letter_templates'
            ]
            for key in root_keys:
                if key in cv_data:
                    pi_data[key] = cv_data[key]

            # Import data to database
            personal_info = PersonalInfo(**pi_data)
            db.session.add(personal_info)
            
            for exp in cv_data.get('work_experience', []):
                experience = Experience(**exp)
                db.session.add(experience)
            
            for edu in cv_data.get('education', []):
                education = Education(**edu)
                db.session.add(education)
            
    # Commit all pending changes to the database
    try:
        db.session.commit()
    except Exception as e:
        logging.error(f"Database setup failed: {e}")
        db.session.rollback()

@app.cli.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    with app.app_context():
        setup_database()
    click.echo("Initialized the database.")

# Initialize database when app starts (but won't overwrite existing data)
with app.app_context():
    setup_database()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/')
@login_required
def index():
    personal_info = PersonalInfo.query.first()
    experiences = Experience.query.all()
    education = Education.query.all()
    return render_template('index.html', 
                         personal_info=personal_info,
                         experiences=experiences,
                         education=education)

@app.route('/convert', methods=['GET', 'POST'])
@login_required
def convert():
    if request.method == 'POST':
        content = request.form.get('content')
        input_format = request.form.get('input_format')

        if not content:
            flash('Content cannot be empty.', 'danger')
            return redirect(url_for('convert'))

        html_content = ""
        try:
            if input_format == 'md':
                html_content = markdown2.markdown(content, extras=["fenced-code-blocks", "tables", "strike"])
            elif input_format == 'html':
                # Basic validation for HTML
                if not re.search(r'<html.*?>', content, re.IGNORECASE) or not re.search(r'<body.*?>', content, re.IGNORECASE):
                     flash('Invalid HTML format. Please provide a full HTML document structure.', 'danger')
                     return render_template('convert.html', error='Invalid HTML format. It must contain <html> and <body> tags.')
                html_content = content
            else:
                flash('Invalid format selected.', 'danger')
                return redirect(url_for('convert'))

            # For Markdown, wrap in basic HTML with styles. For HTML, inject styles.
            if input_format == 'md':
                final_html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>Converted Document</title>
                    <style>{generic_styles}</style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
            else: # input_format == 'html'
                # Inject styles into the head of the existing HTML
                if '</head>' in content:
                    final_html = content.replace('</head>', f'<style>{generic_styles}</style></head>', 1)
                else:
                    # If no head tag, just wrap it. Might not be perfect but better than nothing.
                    final_html = f"<html><head><style>{generic_styles}</style></head>{content}</html>"


            output_dir = os.path.join(app.root_path, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = int(datetime.now().timestamp())
            filename = f"converted_{current_user.id}_{timestamp}.pdf"
            filepath = os.path.join(output_dir, filename)

            pdfkit.from_string(final_html, filepath, configuration=PDFKIT_CONFIG)

            return send_from_directory(output_dir, filename, as_attachment=True)

        except Exception as e:
            logging.error(f"PDF conversion failed: {e}")
            flash(f"An error occurred during PDF conversion: {e}", 'danger')
            # Using render_template to show the error on the same page without losing content
            return render_template('convert.html', error=str(e))

    return render_template('convert.html')

@app.route('/save_cv', methods=['POST'])
@login_required
def save_cv():
    try:
        # First, log the incoming request data
        data = request.get_json()
        if not data:
            logging.error("No JSON data received in request")
            return jsonify({
                'status': 'error',
                'message': 'No data received'
            }), 400

        logging.info("Received data structure: %s", list(data.keys()))
        
        # --- Update PersonalInfo ---
        try:
            pi_data = data.get('personal_info', {})
            logging.info("Processing personal_info with fields: %s", list(pi_data.keys()))
            
            personal_info = PersonalInfo.query.first()
            if not personal_info:
                personal_info = PersonalInfo()
                db.session.add(personal_info)
                logging.info("Created new PersonalInfo record")
            else:
                logging.info("Updating existing PersonalInfo record")

            # Direct field mapping
            fields_to_update = [
                'full_name', 'preferred_name', 'email', 'phone', 'location',
                'portfolio', 'behance_portfolio', 'github', 'linkedin',
                'summary', 'design_philosophy', 'references'
            ]
            
            for field in fields_to_update:
                try:
                    if field in pi_data:
                        setattr(personal_info, field, pi_data.get(field))
                        logging.debug("Updated %s to: %s", field, pi_data.get(field))
                except Exception as e:
                    logging.error(f"Error updating field {field}: {str(e)}")
                    raise

            # Handle JSON fields
            json_fields = [
                'title', 'willing_to_relocate', 'languages', 'skills',
                'professional_attributes', 'possible_titles'
            ]
            
            for field in json_fields:
                try:
                    if field in pi_data:
                        value = pi_data.get(field)
                        if isinstance(value, (dict, list)):
                            setattr(personal_info, field, value)
                            logging.debug("Updated JSON field %s", field)
                except Exception as e:
                    logging.error(f"Error updating JSON field {field}: {str(e)}")
                    raise

        except Exception as e:
            logging.error("Error processing personal info: %s", str(e))
            raise

        # --- Update Experiences ---
        try:
            logging.info("Processing %d experiences", len(data.get('experience', [])))
            Experience.query.delete()
            for exp_data in data.get('experience', []):
                exp = Experience(
                    title=exp_data.get('title'),
                    company=exp_data.get('company'),
                    location=exp_data.get('location'),
                    period_start=exp_data.get('period_start'),
                    period_end=exp_data.get('period_end'),
                    responsibilities=exp_data.get('responsibilities', []),
                    highlights=exp_data.get('highlights', [])
                )
                db.session.add(exp)
                logging.debug("Added experience: %s at %s", exp_data.get('title'), exp_data.get('company'))
        except Exception as e:
            logging.error("Error processing experiences: %s", str(e))
            raise
        
        # --- Update Education ---
        try:
            logging.info("Processing %d education entries", len(data.get('education', [])))
            Education.query.delete()
            for edu_data in data.get('education', []):
                edu = Education(
                    degree=edu_data.get('degree'),
                    institution=edu_data.get('institution'),
                    specialization=edu_data.get('specialization'),
                    location=edu_data.get('location'),
                    period=edu_data.get('period'),
                    highlights=edu_data.get('highlights', [])
                )
                db.session.add(edu)
                logging.debug("Added education: %s at %s", edu_data.get('degree'), edu_data.get('institution'))
        except Exception as e:
            logging.error("Error processing education: %s", str(e))
            raise
        
        try:
            db.session.commit()
            logging.info("Successfully saved all CV data")
            
            return jsonify({
                'status': 'success',
                'message': 'CV data has been saved successfully!'
            })
        except Exception as e:
            logging.error("Error committing to database: %s", str(e))
            db.session.rollback()
            raise

    except Exception as e:
        db.session.rollback()
        logging.error("Error saving CV data: %s", str(e), exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"An error occurred while saving: {str(e)}"
        }), 500

@app.route('/job_application')
@login_required
def job_application():
    return render_template('job_application.html')

def clean_and_parse_json(response_text):
    """Cleans the Gemini response to extract a valid JSON object."""
    # Find the JSON block, even with potential markdown wrappers
    match = re.search(r'```(json)?(.*)```', response_text, re.DOTALL)
    if match:
        # Group 2 will capture the content, whether 'json' is present or not
        json_str = match.group(2).strip()
    else:
        # Fallback for when there's no wrapper
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
        else:
            raise ValueError("No valid JSON object found in the response.")
            
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        logging.error(f"Problematic JSON string: \\n{json_str}")
        raise ValueError("Invalid JSON received from the model.")

def json_to_cv_markdown(data):
    """Converts a CV JSON object to a robust Markdown string."""
    parts = []

    # Personal Info
    personal_info = data.get('personal_info', {})
    
    # Header with Name and Title
    if personal_info.get('full_name'):
        parts.append(f"# {personal_info['full_name']}")
    if personal_info.get('title'):
        parts.append(f"**{personal_info['title']}**")
    
    # Contact Details
    contact_info = []
    if personal_info.get('location'):
        contact_info.append(personal_info['location'])
    if personal_info.get('phone'):
        contact_info.append(personal_info['phone'])
    if personal_info.get('email'):
        contact_info.append(personal_info['email'])
    
    if contact_info:
        parts.append(" | ".join(contact_info))

    # Links
    links_info = []
    if personal_info.get('portfolio'):
        links_info.append(f"**Portfolio:** {personal_info['portfolio']}")
    if personal_info.get('github'):
        links_info.append(f"**GitHub:** {personal_info['github']}")
    if personal_info.get('linkedin'):
        links_info.append(f"**LinkedIn:** {personal_info['linkedin']}")
        
    if links_info:
        parts.append(" | ".join(links_info))

    parts.append("\n---")

    # Summary
    if data.get('summary'):
        parts.append("## Professional Summary")
        parts.append(data['summary'])

    # Experience
    if data.get('experience'):
        parts.append("## Experience")
        for exp in data.get('experience', []):
            exp_parts = [
                f"### {exp.get('title')}",
                f"*{exp.get('company', '')} | {exp.get('location', '')} | {exp.get('period', '')}*"
            ]
            exp_parts.extend([f"- {resp}" for resp in exp.get('responsibilities', [])])
            parts.append("\\n".join(exp_parts))

    # Education
    if data.get('education'):
        parts.append("## Education")
        for edu in data.get('education', []):
            edu_parts = [f"### {edu.get('degree')}", f"*{edu.get('institution', '')} | {edu.get('period', '')}*"]
            edu_parts.extend([f"- {detail}" for detail in edu.get('details', [])])
            parts.append("\\n".join(edu_parts))
            
    # Hardcoded Languages (Skills section is now removed)
    parts.append("## Languages")
    parts.append("English: Fluent, Cantonese: Fluent, Mandarin: Fluent")

    return "\\n\\n".join(parts)

def cleanup_output_folder(folder_path, max_files_per_type=10):
    """Deletes the oldest PDFs in the output folder if the count exceeds the limit."""
    try:
        files = os.listdir(folder_path)
        
        # Separate files by type (CV or CL)
        cv_files = [f for f in files if f.startswith('CV_') and f.endswith('.pdf')]
        cl_files = [f for f in files if f.startswith('CL_') and f.endswith('.pdf')]
        
        # Clean up CV files
        if len(cv_files) > max_files_per_type:
            # Sort by creation time (oldest first)
            cv_files.sort(key=lambda f: os.path.getctime(os.path.join(folder_path, f)))
            # Calculate how many to delete
            num_to_delete = len(cv_files) - max_files_per_type
            # Delete the oldest files
            for i in range(num_to_delete):
                os.remove(os.path.join(folder_path, cv_files[i]))
                print(f"Deleted old CV: {cv_files[i]}")

        # Clean up CL files
        if len(cl_files) > max_files_per_type:
            cl_files.sort(key=lambda f: os.path.getctime(os.path.join(folder_path, f)))
            num_to_delete = len(cl_files) - max_files_per_type
            for i in range(num_to_delete):
                os.remove(os.path.join(folder_path, cl_files[i]))
                print(f"Deleted old CL: {cl_files[i]}")

    except OSError as e:
        print(f"Error during cleanup: {e}")

def merge_cl_cv_pdf(cl_path, cv_path, output_path):
    """Merges cover letter and CV into a single PDF file with cover letter as the first page."""
    try:
        merger = PdfMerger()
        
        # Add cover letter as first page
        merger.append(cl_path)
        # Add CV as subsequent pages
        merger.append(cv_path)
        
        # Write to output file
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
            
        return True
    except Exception as e:
        logging.error(f"Error merging PDFs: {e}")
        return False

def json_to_cl_markdown(data):
    """Converts a Cover Letter JSON object to a robust Markdown string."""
    # The new prompt returns H3s directly in the JSON values
    parts = [
        data.get('greeting', ''),
        "\\n\\n".join(data.get('body', [])),
        data.get('closing', ''),
        data.get('signature', '')
    ]
    return "\\n\\n".join(filter(None, parts))

def unified_generate_content(prompt, model_type='gemini', **kwargs):
    """
    Try Gemini first, fallback to OpenAI on 429/500 errors.
    """
    try:
        if model_type == 'gemini':
            response = model.generate_content(prompt, **kwargs)
            return response
    except Exception as e:
        # Gemini API error handling
        if hasattr(e, 'status_code') and e.status_code in [429, 500]:
            logging.warning(f"Gemini error {e.status_code}, fallback to OpenAI.")
        elif '429' in str(e) or '500' in str(e):
            logging.warning(f"Gemini error: {e}, fallback to OpenAI.")
        else:
            raise  # Other errors不處理
        # fallback to OpenAI
        try:
            completion = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2048)
            )
            class DummyResponse:
                def __init__(self, text):
                    self.text = text
            return DummyResponse(completion.choices[0].message.content)
        except Exception as oe:
            logging.error(f"OpenAI fallback also failed: {oe}")
            raise

def process_job_application(job_description, job_source='indeed'):
    """Process job application and generate all necessary documents."""
    try:
        # --- Step 1: Extract Job Title and Company from Job Description ---
        try:
            job_info_prompt = f"""
            Analyze the following job description and extract the job title and the company name.
            Return the information in a JSON object with the keys "job_title" and "company_name".
            If a value is not found, return "N/A".

            Job Description:
            ---
            {job_description}
            ---
            """
            job_info_response = unified_generate_content(job_info_prompt)
            json_text = re.sub(r'```json\s*|\s*```', '', job_info_response.text.strip())
            job_info = json.loads(json_text)
            job_title = job_info.get('job_title', 'Job')
            company_name = job_info.get('company_name', 'Company')
        except Exception as e:
            logging.error(f"Error extracting job info: {e}")
            job_title = "Job"
            company_name = "Company"

        # --- Sanitize job title for filename ---
        def sanitize_filename(name):
            name = re.sub(r'[\\/*?:"<>|]', "", name)
            name = name.replace(' ', '_')
            return name

        safe_job_title = sanitize_filename(job_title)
        personal_info = PersonalInfo.query.first()
        experiences = Experience.query.all()
        education = Education.query.all()

        if not personal_info:
            return {'status': 'error', 'message': 'No CV data found.'}, 404

        # Prepare CV data
        cv_data = {
            'personal_info': {
                'full_name': personal_info.full_name,
                'preferred_name': personal_info.preferred_name,
                'title': personal_info.title,
                'phone': personal_info.phone,
                'email': personal_info.email,
                'location': personal_info.location,
                'willing_to_relocate': personal_info.willing_to_relocate,
                'portfolio': personal_info.portfolio,
                'behance_portfolio': personal_info.behance_portfolio,
                'github': personal_info.github,
                'linkedin': personal_info.linkedin,
                'languages': personal_info.languages,
                'summary': personal_info.summary,
                'design_philosophy': personal_info.design_philosophy,
                'skills': personal_info.skills,
                'professional_attributes': personal_info.professional_attributes,
                'references': personal_info.references
            },
            'experience': [{
                'title': exp.title,
                'company': exp.company,
                'location': exp.location,
                'period_start': exp.period_start,
                'period_end': exp.period_end,
                'responsibilities': exp.responsibilities,
                'highlights': exp.highlights
            } for exp in experiences],
            'education': [{
                'degree': edu.degree,
                'specialization': edu.specialization,
                'institution': edu.institution,
                'location': edu.location,
                'period': edu.period,
                'highlights': edu.highlights
            } for edu in education]
        }

        job_details = {'description': job_description, 'source': job_source}

        # Generate documents
        from prompts.cv_prompt import get_cv_prompt
        cv_prompt = get_cv_prompt(job_details, cv_data)
        cv_response = unified_generate_content(cv_prompt)
        cv_json = clean_and_parse_json(cv_response.text)
        cv_md = json_to_cv_markdown(cv_json)
        cv_md = cv_md.replace("\\n", "\n")

        from prompts.cl_prompt import get_cl_prompt
        cl_prompt = get_cl_prompt(job_details, cv_data)
        cl_response = unified_generate_content(cl_prompt)
        cl_json = clean_and_parse_json(cl_response.text)
        cover_letter_md = json_to_cl_markdown(cl_json)
        cover_letter_md = cover_letter_md.replace("\\n", "\n")

        from prompts.cn_prompt import get_cn_prompt
        cn_prompt = get_cn_prompt(cover_letter_md)
        cn_response = unified_generate_content(cn_prompt)
        chinese_cover_letter_md = cn_response.text.strip()
        chinese_cover_letter_md = chinese_cover_letter_md.replace("\\n", "\n")

        # Generate PDFs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(app.instance_path, 'output')
        os.makedirs(output_dir, exist_ok=True)

        extras = ["tables", "break-on-newline", "cuddled-lists", "fenced-code-blocks", "header-ids", "markdown-in-html", "metadata", "strike", "task_list"]
        cv_html_content = markdown2.markdown(cv_md, extras=extras)
        cover_letter_en_html_content = markdown2.markdown(cover_letter_md, extras=extras)
        cover_letter_zh_html_content = markdown2.markdown(chinese_cover_letter_md, extras=extras)

        cv_html = render_template('pdf_template.html', content=cv_html_content)
        cover_letter_en_html = render_template('letter_template.html', content=cover_letter_en_html_content)
        cover_letter_zh_html = render_template('letter_template.html', content=cover_letter_zh_html_content)

        pdf_options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }

        # Generate PDF files
        cv_pdf = pdfkit.from_string(cv_html, False, configuration=PDFKIT_CONFIG, options=pdf_options)
        cv_filename = f'cv_{safe_job_title}_{timestamp}.pdf'
        cv_path = os.path.join(output_dir, cv_filename)
        with open(cv_path, 'wb') as f:
            f.write(cv_pdf)

        cl_en_pdf = pdfkit.from_string(cover_letter_en_html, False, configuration=PDFKIT_CONFIG, options=pdf_options)
        cl_en_filename = f'cover_letter_en_{safe_job_title}_{timestamp}.pdf'
        cl_en_path = os.path.join(output_dir, cl_en_filename)
        with open(cl_en_path, 'wb') as f:
            f.write(cl_en_pdf)

        cl_zh_pdf = pdfkit.from_string(cover_letter_zh_html, False, configuration=PDFKIT_CONFIG, options=pdf_options)
        cl_zh_filename = f'cover_letter_zh_{safe_job_title}_{timestamp}.pdf'
        cl_zh_path = os.path.join(output_dir, cl_zh_filename)
        with open(cl_zh_path, 'wb') as f:
            f.write(cl_zh_pdf)

        # Generate merged PDF
        merged_filename = f'merged_application_{safe_job_title}_{timestamp}.pdf'
        merged_path = os.path.join(output_dir, merged_filename)
        merge_success = merge_cl_cv_pdf(cl_en_path, cv_path, merged_path)

        # Get server URL from environment or use default
        server_url = os.getenv('SERVER_URL', 'http://localhost:5001')
        
        # Return file URLs with full server URL
        return {
            'status': 'success',
            'cv_md': cv_md,
            'cover_letter_en_md': cover_letter_md,
            'cover_letter_zh_md': chinese_cover_letter_md,
            'files': {
                'cv_pdf': f'{server_url}/output/{cv_filename}',
                'cover_letter_en_pdf': f'{server_url}/output/{cl_en_filename}',
                'cover_letter_zh_pdf': f'{server_url}/output/{cl_zh_filename}',
                'merged_pdf': f'{server_url}/output/{merged_filename}' if merge_success else None
            }
        }

    except Exception as e:
        logging.error(f"Error in process_job_application: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/submit_job', methods=['POST'])
@login_required
def submit_job():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400
            
        job_description = data.get('job_description', '')
        job_source = data.get('job_source', '')
        
        if not job_description:
            return jsonify({'status': 'error', 'message': 'Job description is required'}), 400

        result = process_job_application(job_description, job_source)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error in submit_job: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate_application', methods=['POST'])
@require_api_key
def generate_application():
    try:
        logging.info("Received API request for generate_application")
        data = request.get_json()
        logging.info(f"Request data: {data}")
        
        if not data:
            logging.error("No JSON data received")
            return jsonify({
                'status': 'error',
                'message': 'No JSON data received'
            }), 400

        job_description = data.get('job_description', '')
        ad_source = data.get('ad_source', 'indeed')
        
        logging.info(f"Job description length: {len(job_description)}")
        logging.info(f"Ad source: {ad_source}")
        
        # Validate input
        if not job_description or len(job_description.strip()) < 100:
            logging.error(f"Invalid job description length: {len(job_description.strip() if job_description else 0)}")
            return jsonify({
                'status': 'error',
                'message': 'Job Description is not valid. It should be at least 100 characters long.'
            }), 400

        result = process_job_application(job_description, ad_source)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
            
        # Return only the file URLs for API calls
        return jsonify({
            'status': 'success',
            'files': result.get('files', {})
        })
        
    except Exception as e:
        logging.error(f"Error in generate_application: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/output/<path:filename>')
@require_api_key
def static_file(filename):
    """Allow file download for both logged-in users and API users with valid key."""
    output_dir = os.path.join(app.instance_path, 'output')
    try:
        return send_from_directory(output_dir, filename)
    except Exception as e:
        logging.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'File not found or error occurred: {str(e)}'
        }), 404

@app.route('/get_cv', methods=['GET'])
@login_required
def get_cv():
    try:
        personal_info = PersonalInfo.query.first()
        experiences = Experience.query.all()
        education = Education.query.all()

        if not personal_info:
            return jsonify({
                'status': 'error',
                'message': 'No CV data found'
            }), 404

        # Convert to dictionary format
        cv_data = {
            'personal_info': {
                'full_name': personal_info.full_name,
                'preferred_name': personal_info.preferred_name,
                'title': personal_info.title,
                'phone': personal_info.phone,
                'email': personal_info.email,
                'location': personal_info.location,
                'willing_to_relocate': personal_info.willing_to_relocate,
                'portfolio': personal_info.portfolio,
                'behance_portfolio': personal_info.behance_portfolio,
                'github': personal_info.github,
                'linkedin': personal_info.linkedin,
                'languages': personal_info.languages,
                'summary': personal_info.summary,
                'design_philosophy': personal_info.design_philosophy,
                'skills': personal_info.skills,
                'professional_attributes': personal_info.professional_attributes,
                'references': personal_info.references
            },
            'experience': [{
                'title': exp.title,
                'company': exp.company,
                'location': exp.location,
                'period_start': exp.period_start,
                'period_end': exp.period_end,
                'responsibilities': exp.responsibilities,
                'highlights': exp.highlights
            } for exp in experiences],
            'education': [{
                'degree': edu.degree,
                'specialization': edu.specialization,
                'institution': edu.institution,
                'location': edu.location,
                'period': edu.period,
                'highlights': edu.highlights
            } for edu in education]
        }

        return jsonify({
            'status': 'success',
            'data': cv_data
        })

    except Exception as e:
        logging.error(f"Error retrieving CV data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"An error occurred while retrieving CV data: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)