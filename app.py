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

# Configure pdfkit
# Using the user-provided path for wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
try:
    PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
except OSError:
    logging.warning("wkhtmltopdf not found at the specified path. PDF generation will fail.")
    PDFKIT_CONFIG = None

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
    return User.query.get(int(user_id))

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
        data = request.get_json()
        job_description = data.get('job_description')
        job_source = data.get('job_source', 'unknown')  # Get job source from request

        if not job_description:
            return jsonify({
                'status': 'error',
                'message': 'Job description is required'
            }), 400

        # Create output directory if it doesn't exist
        output_dir = os.path.join(app.instance_path, 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Generate base filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"job_application_{timestamp}"

        # Extract job details using Gemini
        job_details_prompt = f"""
        Analyze this job posting from {job_source} and extract the following information in JSON format:
        - company_name
        - position
        - location
        - key_requirements (as a list)
        - preferred_qualifications (as a list)
        - company_description (brief)
        
        Job posting:
        {job_description}
        
        Respond with ONLY the JSON object, no other text or explanations.
        """

        try:
            job_details_response = model.generate_content(job_details_prompt)
            # Clean the response text before parsing
            cleaned_text = job_details_response.text.strip()
            # Remove any markdown code block markers
            cleaned_text = re.sub(r'```json\s*|\s*```', '', cleaned_text)
            # Remove any HTML tags
            cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
            # Fix any invalid JSON escape sequences
            cleaned_text = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', cleaned_text)
            
            try:
                job_details = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse job details JSON: {e}")
                logging.error(f"Cleaned text: {cleaned_text}")
                # Create a basic job details structure if parsing fails
                job_details = {
                    "company_name": "Unknown Company",
                    "position": "Unknown Position",
                    "location": "Unknown Location",
                    "key_requirements": [],
                    "preferred_qualifications": [],
                    "company_description": "No description available"
                }
        except Exception as e:
            logging.error(f"Error generating job details: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating job details: {str(e)}'
            }), 500

        # Generate CV using Gemini
        cv_prompt = f"""
        Create a professional CV optimized for this {job_source} job posting. The CV should:
        1. Highlight relevant skills and experiences that match the job requirements
        2. Use clear, professional language
        3. Include all necessary sections (Personal Info, Experience, Education, Skills)
        4. Be formatted in Markdown
        5. Use actual content instead of placeholders
        6. Be concise and impactful

        Job Details:
        {json.dumps(job_details, indent=2)}

        Respond with ONLY the Markdown content, no explanations or additional text.
        """

        try:
            cv_response = model.generate_content(cv_prompt)
            cv_md = cv_response.text.strip()
            # Remove any markdown code block markers
            cv_md = re.sub(r'```markdown\s*|\s*```', '', cv_md)
        except Exception as e:
            logging.error(f"Error generating CV: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating CV: {str(e)}'
            }), 500

        # Generate English cover letter
        cl_en_prompt = f"""
        Create a professional cover letter in English for this {job_source} job posting. The letter should:
        1. Be addressed to the company
        2. Highlight relevant qualifications and experiences
        3. Show enthusiasm for the position
        4. Be formatted in Markdown
        5. Use actual content instead of placeholders
        6. Be concise and impactful

        Job Details:
        {json.dumps(job_details, indent=2)}

        Respond with ONLY the Markdown content, no explanations or additional text.
        """

        try:
            cl_en_response = model.generate_content(cl_en_prompt)
            cl_en_md = cl_en_response.text.strip()
            # Remove any markdown code block markers
            cl_en_md = re.sub(r'```markdown\s*|\s*```', '', cl_en_md)
        except Exception as e:
            logging.error(f"Error generating English cover letter: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating English cover letter: {str(e)}'
            }), 500

        # Generate Chinese cover letter
        cl_zh_prompt = f"""
        Create a professional cover letter in Traditional Chinese for this {job_source} job posting. The letter should:
        1. Be addressed to the company
        2. Highlight relevant qualifications and experiences
        3. Show enthusiasm for the position
        4. Be formatted in Markdown
        5. Use actual content instead of placeholders
        6. Be concise and impactful

        Job Details:
        {json.dumps(job_details, indent=2)}

        Respond with ONLY the Markdown content, no explanations or additional text.
        """

        try:
            cl_zh_response = model.generate_content(cl_zh_prompt)
            cl_zh_md = cl_zh_response.text.strip()
            # Remove any markdown code block markers
            cl_zh_md = re.sub(r'```markdown\s*|\s*```', '', cl_zh_md)
        except Exception as e:
            logging.error(f"Error generating Chinese cover letter: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating Chinese cover letter: {str(e)}'
            }), 500

        # Prepare the result
        result = {
            'job_details': job_details,
            'cv_md': cv_md,
            'cover_letter_en_md': cl_en_md,
            'cover_letter_zh_md': cl_zh_md
        }

        # Save files
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_name = secure_filename(result['job_details'].get('company_name', 'UnknownCompany'))
        position = secure_filename(result['job_details'].get('position', 'UnknownPosition'))
        base_filename = f"{timestamp}_{company_name}_{position}"

        def generate_pdf(markdown_content, template, output_filename):
            try:
                # Convert Markdown to HTML
                html_fragment = markdown2.markdown(markdown_content)
                
                # Render full HTML with template
                full_html = render_template(template, content=html_fragment)
                
                # Generate PDF
                pdf_path = os.path.join(output_dir, output_filename)
                if PDFKIT_CONFIG:
                    pdfkit.from_string(
                        full_html, 
                        pdf_path,
                        configuration=PDFKIT_CONFIG,
                        options={
                            'encoding': 'utf-8',
                            'margin-top': '20mm',
                            'margin-right': '20mm',
                            'margin-bottom': '20mm',
                            'margin-left': '20mm',
                            'page-size': 'A4'
                        }
                    )
                    return pdf_path
                else:
                    logging.error("PDFKit configuration not found")
                    return None
            except Exception as e:
                logging.error(f"PDF generation failed: {e}")
                return None

        # Generate PDFs for all documents
        cv_pdf = generate_pdf(
            result.get('cv_md', ''),
            'pdf_template.html',
            f"{base_filename}_CV.pdf"
        )
        
        cl_en_pdf = generate_pdf(
            result.get('cover_letter_en_md', ''),
            'letter_template.html',
            f"{base_filename}_Cover_Letter_EN.pdf"
        )
        
        cl_zh_pdf = generate_pdf(
            result.get('cover_letter_zh_md', ''),
            'letter_template.html',
            f"{base_filename}_Cover_Letter_ZH.pdf"
        )

        # Save Markdown files for reference
        def save_markdown(content, filename):
            path = os.path.join(output_dir, filename)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return path

        cv_md_path = save_markdown(result.get('cv_md', ''), f"{base_filename}_CV.md")
        cl_en_md_path = save_markdown(result.get('cover_letter_en_md', ''), f"{base_filename}_Cover_Letter_EN.md")
        cl_zh_md_path = save_markdown(result.get('cover_letter_zh_md', ''), f"{base_filename}_Cover_Letter_ZH.md")

        # Save job application details to the database
        new_application = JobApplication(
            company_name=result['job_details'].get('company_name'),
            position=result['job_details'].get('position'),
            location=result['job_details'].get('location'),
            job_description=job_description,
            cv_path=cv_pdf,
            cover_letter_en_path=cl_en_pdf,
            cover_letter_zh_path=cl_zh_pdf
        )
        db.session.add(new_application)
        db.session.commit()

        # Prepare response for the frontend
        response_data = {
            'status': 'success',
            'markdown': {
                'cv_md': result.get('cv_md', ''),
                'cover_letter_en_md': result.get('cover_letter_en_md', ''),
                'cover_letter_zh_md': result.get('cover_letter_zh_md', '')
            },
            'files': {
                'cv_pdf': url_for('static_file', filename=os.path.basename(cv_pdf)) if cv_pdf else None,
                'cover_letter_en_pdf': url_for('static_file', filename=os.path.basename(cl_en_pdf)) if cl_en_pdf else None,
                'cover_letter_zh_pdf': url_for('static_file', filename=os.path.basename(cl_zh_pdf)) if cl_zh_pdf else None
            }
        }
        
        return jsonify(response_data)
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/output/<path:filename>')
@login_required
def static_file(filename):
    return send_from_directory('output', filename)

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