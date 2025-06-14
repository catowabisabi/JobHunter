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

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

genai.configure(api_key=GOOGLE_API_KEY)

# List available models
""" try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Available model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}") """

# Use gemini-1.0-pro as it's the most stable version
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
model = genai.GenerativeModel(GEMINI_MODEL)

# Configure PDFKit
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')

# Use instance_relative_config to let Flask know the instance folder exists
app = Flask(__name__, instance_relative_config=True)

# Setup logging
logging.basicConfig(level=logging.INFO)

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
        default_user.set_password('admin')
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
    setup_database()
    click.echo("Initialized the database.")

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

@app.route('/submit_job', methods=['POST'])
@login_required
def submit_job():
    try:
        # Get job details from request
        job_description = request.json.get('job_description', '')
        job_source = request.json.get('job_source', '')
        
        if not job_description:
            return jsonify({
                'status': 'error',
                'message': 'Job description is required'
            }), 400

        # Get CV data from database
        personal_info = PersonalInfo.query.first()
        experiences = Experience.query.all()
        education = Education.query.all()

        if not personal_info:
            return jsonify({
                'status': 'error',
                'message': 'No CV data found. Please create your CV first.'
            }), 404

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

        # Prepare job details
        job_details = {
            'description': job_description,
            'source': job_source
        }

        # Generate CV using Gemini
        from prompts.cv_prompt import get_cv_prompt
        cv_prompt = get_cv_prompt(job_details, cv_data)

        try:
            cv_response = model.generate_content(cv_prompt)
            cv_md = cv_response.text.strip()
            cv_md = re.sub(r'```markdown\s*|\s*```', '', cv_md)
            print(cv_md)
        except Exception as e:
            logging.error(f"Error generating CV: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating CV: {str(e)}'
            }), 500

        # Generate English Cover Letter using Gemini
        from prompts.cl_prompt import get_cl_prompt
        cover_letter_prompt = get_cl_prompt(job_details, cv_data)

        try:
            cover_letter_response = model.generate_content(cover_letter_prompt)
            cover_letter_md = cover_letter_response.text.strip()
            cover_letter_md = re.sub(r'```markdown\s*|\s*```', '', cover_letter_md)
            cover_letter_md = cover_letter_md.replace('```html', '').replace('```', '')
            cover_letter_md = cover_letter_md.replace('html', '')
            print(cover_letter_md)
        except Exception as e:
            logging.error(f"Error generating cover letter: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating cover letter: {str(e)}'
            }), 500

        # Generate Chinese Cover Letter using Gemini
        from prompts.cn_prompt import get_cn_prompt
        chinese_cover_letter_prompt = get_cn_prompt(cover_letter_md)

        try:
            chinese_cover_letter_response = model.generate_content(chinese_cover_letter_prompt)
            chinese_cover_letter_md = chinese_cover_letter_response.text.strip()
            chinese_cover_letter_md = re.sub(r'```markdown\s*|\s*```', '', chinese_cover_letter_md)
            chinese_cover_letter_md = chinese_cover_letter_md.replace('html', '')
        except Exception as e:
            logging.error(f"Error generating Chinese cover letter: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating Chinese cover letter: {str(e)}'
            }), 500

        # Generate PDFs
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(app.instance_path, 'output')
            os.makedirs(output_dir, exist_ok=True)

            # Convert Markdown to HTML
            cv_html = markdown2.markdown(cv_md, extras=["tables", "break-on-newline"])
            cover_letter_en_html = markdown2.markdown(cover_letter_md, extras=["tables", "break-on-newline"])
            cover_letter_zh_html = markdown2.markdown(chinese_cover_letter_md, extras=["tables", "break-on-newline"])

            # Add CSS styles
            html_style = """
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                }
                h1, h2 {
                    color: #2c3e50;
                }
                h1 {
                    border-bottom: 2px solid #2c3e50;
                    padding-bottom: 10px;
                }
                h2 {
                    margin-top: 20px;
                }
                p {
                    margin: 10px 0;
                }
                ul {
                    margin: 10px 0;
                    padding-left: 20px;
                }
                .flex-container {
                    display: flex;
                    gap: 2em;
                }
                .left-column {
                    flex: 35;
                }
                .right-column {
                    flex: 65;
                }
            </style>
            """

            cv_html = f"{html_style}<div class='document'>{cv_html}</div>"
            cover_letter_en_html = f"{html_style}<div class='document'>{cover_letter_en_html}</div>"
            cover_letter_zh_html = f"{html_style}<div class='document'>{cover_letter_zh_html}</div>"

            # Generate CV PDF
            cv_pdf = pdfkit.from_string(cv_html, False, configuration=PDFKIT_CONFIG, options={
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            })
            cv_filename = f'cv_{timestamp}.pdf'
            cv_path = os.path.join(output_dir, cv_filename)
            with open(cv_path, 'wb') as f:
                f.write(cv_pdf)

            # Generate English Cover Letter PDF
            cl_en_pdf = pdfkit.from_string(cover_letter_en_html, False, configuration=PDFKIT_CONFIG, options={
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            })
            cl_en_filename = f'cover_letter_en_{timestamp}.pdf'
            cl_en_path = os.path.join(output_dir, cl_en_filename)
            with open(cl_en_path, 'wb') as f:
                f.write(cl_en_pdf)

            # Generate Chinese Cover Letter PDF
            cl_zh_pdf = pdfkit.from_string(cover_letter_zh_html, False, configuration=PDFKIT_CONFIG, options={
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            })
            cl_zh_filename = f'cover_letter_zh_{timestamp}.pdf'
            cl_zh_path = os.path.join(output_dir, cl_zh_filename)
            with open(cl_zh_path, 'wb') as f:
                f.write(cl_zh_pdf)

            return jsonify({
                'status': 'success',
                'cv_md': cv_md,
                'cover_letter_en_md': cover_letter_md,
                'cover_letter_zh_md': chinese_cover_letter_md,
                'files': {
                    'cv_pdf': f'/output/{cv_filename}',
                    'cover_letter_en_pdf': f'/output/{cl_en_filename}',
                    'cover_letter_zh_pdf': f'/output/{cl_zh_filename}'
                }
            })
        except Exception as e:
            logging.error(f"Error generating PDFs: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating PDFs: {str(e)}'
            }), 500

    except Exception as e:
        logging.error(f"Error in job application: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/output/<path:filename>')
@login_required
def static_file(filename):
    output_dir = os.path.join(app.instance_path, 'output')
    return send_from_directory(output_dir, filename)

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
    app.run(debug=True)