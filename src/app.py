import os
from datetime import timedelta

from app_logger import logger
from app_validator import QueryResponse
from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_cors import cross_origin
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from genai_service import GenAIService
from pydantic import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash, safe_join
from werkzeug.utils import secure_filename

# Check if .env file exists in the current directory
dotenv_path = find_dotenv()

# If .env file is not found, use /etc/secrets/config
if not dotenv_path:
    dotenv_path = find_dotenv("/etc/secrets/config")

load_dotenv(dotenv_path)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "./data/"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

users = {
    os.environ.get("USERNAME"): generate_password_hash(
        os.environ.get("PASSWORD")
    )
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def user_loader(user_id):
    return User(user_id)


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    if username not in users:
        return None
    user = User(username)
    user.is_authenticated = check_password_hash(
        users.get(username), request.form["password"]
    )
    return user


@app.route("/login", methods=["GET", "POST"])
@cross_origin()
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and check_password_hash(users.get(username), password):
            user = User(username)
            status = login_user(user, remember=True, duration=timedelta(minutes=5))
            logger.info(f"User {username} logged in status: {status}")
            return jsonify(success=True), 200
        logger.info("invald username or password")
        return jsonify(success=False, error="Invalid username or password"), 400
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
@cross_origin()
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/is_authenticated")
def is_authenticated():
    return jsonify({"is_authenticated": current_user.is_authenticated})


genai_service = GenAIService(
    app_key=os.environ.get("OPENAI_API_KEY"),
    pvt_key_base64=os.environ.get("PVT_KEY_BASE64"),
    ca_path=os.environ.get("CA_PATH"),
)

@app.route('/')
@cross_origin()
def index():
    return render_template('index.html')

def escape(s, quote=None):
    """Replace special characters "&", "<" and ">" to HTML-safe sequences.
        If the optional flag quote is true, the quotation mark character (")
    is also translated."""
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
    return s

@app.route('/ask', methods=['POST'])
@cross_origin()
def ask():
    try:
        logger.info("start the execution")
        data = request.get_json(force=True)
        query = escape(data.get("query"))
        response_data = genai_service.get_llm_response(query)
        return jsonify(QueryResponse(response=response_data, error=None).model_dump())
    except ValidationError as e:
        return jsonify(QueryResponse(response=None, error=str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(QueryResponse(response=None, error='Failed to get response from LLM: ' + str(e)).model_dump()), 500


@app.route('/upload', methods=['POST'])
@cross_origin()
@login_required
def upload_file():
    if not current_user.is_authenticated:
        logger.info("User is not authenticated")
        return render_template("login.html")
    if 'file' not in request.files:
        return 'No file uploaded', 400
    file = request.files['file']
    if (
        file.filename.startswith("..")
        or (".." in file.filename)
        or (os.path.basename(file.filename) != file.filename)
    ):
        return "File is unsafe", 400
    if not file.filename.endswith('.pdf') or file.filename == '':
        return 'Only PDF files are allowed', 400
    if file:
        filename = secure_filename(file.filename)
        file_path = safe_join(app.config["UPLOAD_FOLDER"], filename)
        if file_path is None:
            return "File is unsafe", 400
        file.save(file_path)
        logger.info(f"File saved to {file_path}")
        print('File successfully uploaded')
        genai_service.refresh_headers()
        genai_service.db.upload_pdf_file(file_path)
        genai_service.vectordb = genai_service.load_vectordb()
        return 'File successfully uploaded'
    else:
        return 'No file uploaded', 400


@app.route('/load', methods=['GET'])
@cross_origin()
def load_vector_db():
    genai_service.create_vectordb()
    genai_service.vectordb = genai_service.load_vectordb()
    return "loaded the pdf data"


@app.route('/health')
@cross_origin()
def health():
    return 'OK'


# from auth import user


# # Disable browser caching so changes in each step are always shown
# @app.after_request
# def set_response_headers(response):
#     response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response

# @app.route('/', methods=['GET'])
# def main_page():
#     user_email = request.headers.get('X-Goog-Authenticated-User-Email')
#     user_id = request.headers.get('X-Goog-Authenticated-User-ID')

#     verified_email, verified_id = user()

#     page = render_template('index.html',
#         email=user_email,
#         id=user_id,
#         verified_email=verified_email,
#         verified_id=verified_id)
#     return page

# @app.route('/privacy', methods=['GET'])
# def show_policy():
#     page = render_template('privacy.html')
#     return page


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


