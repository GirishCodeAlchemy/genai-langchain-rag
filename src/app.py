import os

from app_logger import logger
from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import cross_origin
from pydantic import ValidationError
from werkzeug.utils import secure_filename
from app_validator import QueryResponse

# Check if .env file exists in the current directory
dotenv_path = find_dotenv()

# If .env file is not found, use /etc/secrets/config
if not dotenv_path:
    dotenv_path = find_dotenv("/etc/secrets/config")

load_dotenv(dotenv_path)

app = Flask(__name__)

genai_service = GenAIService(
    app_key=os.environ.get("OPENAI_API_KEY"),
    pvt_key_base64=os.environ.get("PVT_KEY_BASE64"),
)

@app.route('/')
@cross_origin()
def index():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
@cross_origin()
def ask():
    try:
        logger.info("start the execution")
        data = request.get_json(force=True)
        response_data = genai_service.get_llm_response(query)
        return jsonify(QueryResponse(response=response_data, error=None).model_dump())
    except ValidationError as e:
        return jsonify(QueryResponse(response=None, error=str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(QueryResponse(response=None, error='Failed to get response from LLM: ' + str(e)).model_dump()), 500


@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    file = request.files['file']
    if not file.filename.endswith('.pdf') or file.filename == '':
        return 'Only PDF files are allowed', 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join('./data/', filename))
        print('File successfully uploaded')
        load_vector_db()
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


