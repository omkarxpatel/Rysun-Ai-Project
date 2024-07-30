from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS, cross_origin
import time, json, os, threading, sys
import google.generativeai as genai
from colorama import Fore, init
from dotenv import load_dotenv
from meta_ai_api import MetaAI
from openai import OpenAI
import uuid

load_dotenv()
global_sessions = {}
init(autoreset=True)

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, resources={r"/api/*": {"origins": "*"}})


chatgpt_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
genai.configure(
    api_key=os.environ["BARD_API_KEY"]
)
bard_client = genai.GenerativeModel(os.environ["BARD_MODEL"])
meta_client = MetaAI()


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from screens.email.email_constants import EMAIL_PROMPT_INFO, EMAIL_META_SPECIAL, EMAIL_DEFAULT_VALUES, EMAIL_ROLE_VALUES, EMAIL_PRECON, EMAIL_REGEN_TITLE


##########################################
###              SESSIONS              ###
##########################################

def create_session(uuid):
    print(f"{Fore.GREEN}CREATED SESSION - {uuid}")
    global_sessions[uuid] = {
        'data': {},
        'additional': EMAIL_DEFAULT_VALUES,
        'last_data': {},
        'streaming_results': {}
    }
    print(f"{Fore.BLUE} Global Sessions: {len(global_sessions)}")
    
def delete_session(uuid):
    if uuid in global_sessions:
        del global_sessions[uuid]
        print(f"{Fore.RED}DELETED SESSION - {uuid}")
        print(f"{Fore.BLUE} Global Sessions: {len(global_sessions)}")
        
        # global_sessions = {k: v for k, v in global_sessions.items() if k != 'null'}

        return True
    else:
        return False

def get_session_info(uuid):
    session = global_sessions.get(uuid)
    if session:
        return session
    new_uuid = str(uuid.uuid4())
    create_session(new_uuid)
    return global_sessions[new_uuid]

@app.route('/api/create_session', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def create_session_endpoint():
    session_id = str(uuid.uuid4())
    create_session(session_id)
    return jsonify({'sessionId': session_id}), 200

@app.route('/api/session_info', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def session_info_endpoint():
    session_id = request.headers.get('sessionId')
    if session_id in global_sessions:
        return jsonify(global_sessions[session_id]), 200
    else:
        return jsonify({'error': 'Invalid session ID'}), 403

@app.route('/api/delete_session', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def delete_session_endpoint():
    data = request.get_json()
    session_id = data.get('sessionId')
    if session_id and delete_session(session_id):
        return jsonify({'message': 'Session deleted successfully'}), 200
    else:
        return jsonify({'error': 'Invalid session ID'}), 403

###########################################
###              ENDPOINTS              ###
###########################################

@app.route('/email')
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def serve_email():
    """
    Serves the HTML file for the email generation screen.

    Parameters:
    None

    Returns:
    Response: A response object containing the HTML file for the email generation screen.
    The file is located in the 'screens/email' directory within the project's root path.
    """
    directory = os.path.join(app.root_path, '..', 'screens', 'email')
    return send_from_directory(directory, 'index.html')

@app.route('/code')
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def serve_code():
    """
    Serves the HTML file for the code generation screen.

    Parameters:
    None

    Returns:
    Response: A response object containing the HTML file for the code generation screen.
    The file is located in the 'screens/code' directory within the project's root path.
    """
    directory = os.path.join(app.root_path, '..', 'screens', 'code')
    return send_from_directory(directory, 'index.html')

@app.route('/api/status', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def get_status():
    """
    This function is a route handler for the '/api/status' endpoint.
    It returns a JSON response indicating the status of the server.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the server. In this case, it's 'ok'.
        - HTTP status code: 200 (OK)
    """
    print("ping")
    session_id = request.headers.get('sessionId')
    if not session_id or session_id not in global_sessions:
        # session_id = str(uuid.uuid4())
        # create_session(session_id)
        return jsonify({"status": "Error", "message": "Invalid or missing session ID - navigate to the /email endpoint"}), 403

    session = global_sessions[session_id]
    session['data']['status'] = 'ok'
    return jsonify(session['data']), 200


#####################################
###              GPT              ###
#####################################
def process_gpt(session, preconditional, prompt):
    """
    Processes the GPT model to generate a response.

    Parameters:
    preconditional (str): The precondition for the prompt.
    prompt (str): The user's prompt.

    Returns:
    None
    """
    try:
        prompt_completion = chatgpt_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": preconditional+prompt}
            ]
        )
        
        session['streaming_results']["gpt"] = prompt_completion.choices[0].message.content
        session['streaming_results']["gpt_title"] = str(session['streaming_results']["gpt"].split("\n")[0])
        session['streaming_results']["gpt"] = str("\n".join(session['streaming_results']["gpt"].split("\n")[1:]))
    except Exception as e:
        session['streaming_results']["gpt"] = f"Error: {e}"


@app.route('/api/gpt-regen', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_gpt_regen():
    """
    Handles the GPT regeneration request.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the processing.
        - HTTP status code: 200 (OK)
    """
    try:
        session_id = request.headers.get('sessionId')
        if not session_id or session_id not in global_sessions:
            return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

        session = global_sessions[session_id]
        
        session['streaming_results']["gpt"] = ""

        gpt_thread = threading.Thread(target=process_gpt, args=(session, session['last_data']["precon"], session['last_data']["prompt"]))
        gpt_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/gpt-regen-title', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_gpt_regen_title():
    """
    Handles the GPT regeneration title request.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the processing.
        - 'title': The regenerated title.
        - HTTP status code: 200 (OK)
    """
    try:
        session_id = request.headers.get('sessionId')
        if not session_id or session_id not in global_sessions:
            return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

        session = global_sessions[session_id]
        data = request.get_json()
        gpt_title = data.get("gptTitle", "")
        gpt_response = data.get("gptResponse", "")
        
        if not gpt_response:
            raise ValueError("gptResponse is required")
        
        title = regen_title_gpt(session, gpt_response)
        return jsonify({"status": "Success", "title": title}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "Error", "message": str(e)}), 500

def regen_title_gpt(session, resp):
    """
    Regenerates the title using the GPT model.

    Parameters:
    resp (str): The response to generate the title from.

    Returns:
    str: The regenerated title.
    """
    try:
        prompt_completion = chatgpt_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": EMAIL_REGEN_TITLE + session['streaming_results']["gpt_title"] + resp}
            ]
        )
        
        title = prompt_completion.choices[0].message.content
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
    
    
######################################
###              BARD              ###
######################################

def process_bard(session, preconditional, prompt):
    """
    Processes the Bard model to generate a response.

    Parameters:
    preconditional (str): The precondition for the prompt.
    prompt (str): The user's prompt.

    Returns:
    None
    """
    try:
        preconditional += prompt
        
        bard_result = bard_client.generate_content(preconditional).text
        session['streaming_results']["bard"] = bard_result
        session['streaming_results']["bard_title"] = str(session['streaming_results']["bard"].split("\n")[0])
        session['streaming_results']["bard"] = str("\n".join(session['streaming_results']["bard"].split("\n")[1:]))
        
    except Exception as e:
        session['streaming_results']["bard"] = f"Error: {e}"


@app.route('/api/bard-regen', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_bard_regen():
    """
    Handles the Bard regeneration request.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the processing.
        - HTTP status code: 200 (OK)
    """
    try:
        session_id = request.headers.get('sessionId')
        if not session_id or session_id not in global_sessions:
            return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

        session = global_sessions[session_id]
        session['streaming_results']["bard"] = ""
        
        bard_thread = threading.Thread(target=process_bard, args=(session, session['last_data']["precon"], session['last_data']["prompt"]))
        bard_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/api/bard-regen-title', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_bard_regen_title():
    """
    Handles the Bard regeneration title request.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the processing.
        - 'title': The regenerated title.
        - HTTP status code: 200 (OK)
    """
    try:
        session_id = request.headers.get('sessionId')
        if not session_id or session_id not in global_sessions:
            return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

        session = global_sessions[session_id]
        data = request.get_json()
        bard_title = data.get("bardTitle", "")
        bard_response = data.get("bardResponse", "")
        
        if not bard_response:
            raise ValueError("bardResponse is required")
        
        title = regen_title_bard(session, bard_response)
        return jsonify({"status": "Success", "title": title}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "Error", "message": str(e)}), 500


def regen_title_bard(session, resp):
    """
    Regenerates the title using the Bard model.

    Parameters:
    resp (str): The response to generate the title from.

    Returns:
    str: The regenerated title.
    """
    try:
        title = bard_client.generate_content(EMAIL_REGEN_TITLE + session['streaming_results']["bard_title"] + resp).text
        
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
    
    
######################################
###              META              ###
######################################
    
def process_meta(session, preconditional, prompt):
    """
    Processes the Meta model to generate a response.

    Parameters:
    preconditional (str): The precondition for the prompt.
    prompt (str): The user's prompt.

    Returns:
    None
    """
    try:
        meta_result = meta_client.prompt(message=preconditional + prompt +EMAIL_META_SPECIAL)['message']
        session['streaming_results']["meta"] = meta_result
        val = session['streaming_results']["meta"].split("\n")[0]
        start = 1
        if val[0:7] == "Subject":
            start = 0
            
        session['streaming_results']["meta_title"] = str(session['streaming_results']["meta"].split("\n")[start])
        session['streaming_results']["meta"] = str("\n".join(session['streaming_results']["meta"].split("\n")[start+1:]))
    except Exception as e:
        session['streaming_results']["meta"] = f"Error: {e}"


@app.route('/api/meta-regen', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_meta_regen():
    """
    Handles the Meta regeneration request.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the processing.
        - HTTP status code: 200 (OK)
    """
    try:
        session_id = request.headers.get('sessionId')
        if not session_id or session_id not in global_sessions:
            return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

        session = global_sessions[session_id]
        session['streaming_results']["meta"] = ""

        meta_thread = threading.Thread(target=process_meta, args=(session, session['last_data']["precon"], session['last_data']["prompt"]))
        meta_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/api/meta-regen-title', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_meta_regen_title():
    """
    Handles the Meta regeneration title request.

    Parameters:
    None

    Returns:
    JSON response:
        - 'status': A string indicating the status of the processing.
        - 'title': The regenerated title.
        - HTTP status code: 200 (OK)
    """
    try:
        session_id = request.headers.get('sessionId')
        if not session_id or session_id not in global_sessions:
            return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

        session = global_sessions[session_id]
        data = request.get_json()
        meta_title = data.get("metaTitle", "")
        meta_response = data.get("metaResponse", "")
        
        if not meta_response:
            raise ValueError("metaResponse is required")
        
        title = regen_title_meta(session, meta_response)
        return jsonify({"status": "Success", "title": title}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "Error", "message": str(e)}), 500


def regen_title_meta(session, resp):
    """
    Regenerates the title using the Meta model.

    Parameters:
    resp (str): The response to generate the title from.

    Returns:
    str: The regenerated title.
    """
    try:
        title = meta_client.prompt(message=EMAIL_REGEN_TITLE + session['streaming_results']["meta_title"] + resp)['message']
        
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
    

######################################
###              MAIN              ###
######################################

@app.route('/api/prompt-submission-code', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_prompt_submission_code():
    """
    Handles the prompt submission for code generation.

    Parameters:
    request_data (dict): The request data containing the prompt and language.

    Returns:
    Response: A JSON response indicating the status of the prompt submission.
    If the prompt is not provided, it returns a 400 error with an error message.
    Otherwise, it starts separate threads for GPT, Bard, and Meta models to generate the code.
    """
    session_id = request.headers.get('sessionId')
    if not session_id or session_id not in global_sessions:
        return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

    session = global_sessions[session_id]
    request_data = request.get_json()
    prompt = request_data.get('prompt')
    language = request_data.get('language')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
        
    precon = f"write code for this:\nlanguage:{language}\n\n"
    
    session['last_data']["precon"] = precon
    session['last_data']["prompt"] = prompt

    gpt_thread = threading.Thread(target=process_gpt, args=(session, precon, prompt))
    bard_thread = threading.Thread(target=process_bard, args=(session, precon, prompt))
    meta_thread = threading.Thread(target=process_meta, args=(session, precon, prompt))
    
    gpt_thread.start()
    bard_thread.start()
    meta_thread.start()

    return jsonify({"status": "Processing"}), 200

@app.route('/api/prompt-submission-email', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_prompt_submission_email():

    """
    Handles the prompt submission.

    Parameters:
    request_data (dict): The request data containing the prompt, role, notes, and keywords.

    Returns:
    Response: A JSON response indicating the status of the prompt submission.
    """
    session_id = request.headers.get('sessionId')
    if not session_id or session_id not in global_sessions:
        return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

    session = global_sessions[session_id]
    request_data = request.get_json()
    precon = request_data.get('role') + "\n\n"
    
    prompt = "\n\nPrompt: "
    prompt += request_data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Ensure session['streaming_results'] is initialized
    session['streaming_results'] = {"gpt": "", "bard": "", "meta": ""}

    notes = request_data.get('notes')
    keywords = request_data.get('keywords')
    if session['additional']:
        precon += f"-- Additional info: {session['additional']}" ### CHECK
    if notes:
        precon += f"-- Notes: {notes}"
    if keywords:
        precon += f"-- Keywords: {keywords}"
    precon += f"\n{EMAIL_PROMPT_INFO}"
    
    session['last_data']["precon"] = precon
    session['last_data']["prompt"] = prompt

    def start_thread(target, *args):
        try:
            thread = threading.Thread(target=target, args=args)
            thread.start()
        except Exception as e:
            print(f"Error starting thread for {target.__name__}: {e}")

    start_thread(process_gpt, session, precon, prompt)
    start_thread(process_bard, session, precon, prompt)
    start_thread(process_meta, session, precon, prompt)

    return jsonify({"status": "Processing"}), 200


@app.route('/api/stream-results/<model>', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def stream_results(model):
    """
    Streams the results of the prompt generation for a specific model.

    Parameters:
    model (str): The model for which the results need to be streamed.

    Returns:
    Response: A server-sent event response containing the title and content of the generated prompt.
    """
    session_id = request.args.get('sessionId')  # Get the session ID from query parameters

    if not session_id or session_id not in global_sessions:
        return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

    session = global_sessions[session_id]

    def generate():
        try:
            if model not in session.get('streaming_results', {}):
                session['streaming_results'][model] = ""

            timeout_start = time.time()
            while not session['streaming_results'][model] and time.time() - timeout_start < 15:
                time.sleep(1) ### CHECK

            if time.time() - timeout_start >= 15:
                yield "data: {\"title\": \"None\", \"content\": \"Timeout waiting for results\"}\n\n"
                return

            title = session['streaming_results'].get(f"{model}_title", "None").replace('\n', '`')
            content = session['streaming_results'].get(model, "").replace('\n', '`')
            data = {"title": title, "content": content}
            s = f"data: {json.dumps(data)}\n\n"
            yield s
            return
        
        except Exception as e:
            print(f"Error in streaming results: {e}")

    return Response(generate(), mimetype='text/event-stream')




#######################################
###              OTHER              ###
#######################################
@app.route('/api/model-dropdown-selected', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_model_dropdown_selected():
    """
    Handles the model dropdown selection event.

    Parameters:
    request_json (dict): The request data containing the selected model option.

    Returns:
    JSON response: A JSON response containing the selected model and a message indicating the selection.
    """
    session_id = request.headers.get('sessionId')
    if not session_id or session_id not in global_sessions:
        return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

    session = global_sessions[session_id]
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')

    session['data']['model'] = selected_option
    session['data']['model_selection_message'] = f'Selected model: "{selected_option}"'

    return jsonify(session['data'])


@app.route('/api/role-dropdown-selected', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_role_dropdown_selected():
    """
    Handles the role dropdown selection event.

    Parameters:
    request_json (dict): The request data containing the selected role option.

    Returns:
    JSON response: A JSON response containing the selected role and the corresponding info.
    """
    session_id = request.headers.get('sessionId')
    if not session_id or session_id not in global_sessions:
        return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

    session = global_sessions[session_id]
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown role "{selected_option}" has been selected.')

    session['data']['role'] = selected_option
    session['data']['info'] = EMAIL_ROLE_VALUES.get(selected_option)
    return jsonify(session['data'])


@app.route('/api/selection-choice', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'application/json'])
def handle_selection_choice():
    """
    Handles the selection choice event.

    Parameters:
    request_json (dict): The request data containing the selected option.

    Returns:
    JSON response: A JSON response containing the updated additional options.
    """
    session_id = request.headers.get('sessionId')
    if not session_id or session_id not in global_sessions:
        return jsonify({"status": "Error", "message": "Invalid or missing session ID"}), 403

    session = global_sessions[session_id]
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')

    curr_val = str(selected_option).split()[0]
    for i in range(len(session['additional'])):
        first_val = str(session['additional'][i]).split()[0]
        if curr_val == first_val:
            session['additional'].pop(i)
            break
        
    session['additional'].append(selected_option)
    
    return jsonify(session['data'])



########################################
###              RUNNER              ###
########################################
def run_app_with_retries():
    """
    This function runs the Flask application with error handling.
    If an error occurs during the server's execution, it will be caught and the server will restart after a specified interval.

    Parameters:
    None

    Returns:
    None
    """
    retry_interval = 5
    while True:
        try:
            with app.app_context():
                app.run(host='0.0.0.0', port=5000, debug=True)
        except Exception as e:
            print(f"Server error: {e}. Restarting in {retry_interval} seconds...")
            time.sleep(retry_interval)



if __name__ == '__main__':
    try:
        print(f"{Fore.GREEN}\n\nServer Connected")
        run_app_with_retries()
        
    finally:
        print(f"{Fore.RED}\n\nServer Disconnected")
