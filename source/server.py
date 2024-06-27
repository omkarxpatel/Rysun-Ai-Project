from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv
from meta_ai_api import MetaAI
from flask_cors import CORS
from openai import OpenAI
import google.generativeai as genai
import os
import threading
import time

from screens.email.constants import PROMPT_INFO, META_SPECIAL, DEFAULT_VALUES, ROLE_VALUES, PRECON, REGEN_TITLE


###########################################
###              VARIABLES              ###
###########################################
load_dotenv()
app = Flask(__name__)
CORS(app)

chatgpt_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
genai.configure(api_key=os.environ["BARD_API_KEY"])
bard_client = genai.GenerativeModel('gemini-1.0-pro-latest')
meta_client = MetaAI()

data = {'model': ''}  
additional = DEFAULT_VALUES
last_data = {
    "precon": "",
    "prompt": "",
}
streaming_results = {
    "gpt": "", 
    "gpt_title": "",
    "bard": "", 
    "bard_title":"",
    "meta": "",
    "meta_title":"",
}
streaming_results = {"gpt": "", "bard": "", "meta": ""}

# Server Status
@app.route('/api/status', methods=['GET'])
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
    data['status'] = 'ok'
    return jsonify(data), 200



#####################################
###              GPT              ###
#####################################
def process_gpt(preconditional, prompt, streaming_results):
    """
    Processes the GPT model to generate a response.

    Parameters:
    preconditional (str): The precondition for the prompt.
    prompt (str): The user's prompt.
    streaming_results (dict): The dictionary to store the streaming results.

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
        print(prompt_completion.choices)
        print(preconditional, prompt)
        
        streaming_results["gpt"] = prompt_completion.choices[0].message.content
        streaming_results["gpt_title"] = str(streaming_results["gpt"].split("\n")[0])
        streaming_results["gpt"] = str("\n".join(streaming_results["gpt"].split("\n")[1:]))
        print("GPT result: ", streaming_results["gpt"])
        print(f"\n\nTitle: {streaming_results['gpt_title']}\n\n")
    except Exception as e:
        streaming_results["gpt"] = f"Error: {e}"


@app.route('/api/gpt-regen', methods=['POST'])
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
    global streaming_results
    try:
        streaming_results["gpt"] = ""

        gpt_thread = threading.Thread(target=process_gpt, args=(last_data["precon"], last_data["prompt"], streaming_results))
        gpt_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/gpt-regen-title', methods=['POST'])
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
        data = request.get_json()
        gpt_title = data.get("gptTitle", "")
        gpt_response = data.get("gptResponse", "")
        
        if not gpt_response:
            raise ValueError("gptResponse is required")
        
        title = regen_title_gpt(gpt_response)
        print("title: ", title)
        return jsonify({"status": "Success", "title": title}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "Error", "message": str(e)}), 500

def regen_title_gpt(resp):
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
                {"role": "user", "content": REGEN_TITLE + streaming_results["gpt_title"] + resp}
            ]
        )
        
        title = prompt_completion.choices[0].message.content
        print("regen title,", title)
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
    
    
######################################
###              BARD              ###
######################################

def process_bard(preconditional, prompt, streaming_results):
    """
    Processes the Bard model to generate a response.

    Parameters:
    preconditional (str): The precondition for the prompt.
    prompt (str): The user's prompt.
    streaming_results (dict): The dictionary to store the streaming results.

    Returns:
    None
    """
    try:
        preconditional += prompt
        
        bard_result = bard_client.generate_content(preconditional).text
        
        streaming_results["bard"] = bard_result
        streaming_results["bard_title"] = str(streaming_results["bard"].split("\n")[0])
        streaming_results["bard"] = str("\n".join(streaming_results["bard"].split("\n")[1:]))
        
    except Exception as e:
        streaming_results["bard"] = f"Error: {e}"


@app.route('/api/bard-regen', methods=['POST'])
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
    global streaming_results
    try:
        streaming_results["bard"] = ""

        bard_thread = threading.Thread(target=process_bard, args=(last_data["precon"], last_data["prompt"], streaming_results))
        bard_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/api/bard-regen-title', methods=['POST'])
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
        data = request.get_json()
        bard_title = data.get("bardTitle", "")
        bard_response = data.get("bardResponse", "")
        
        if not bard_response:
            raise ValueError("bardResponse is required")
        
        title = regen_title_bard(bard_response)
        print("title: ", title)
        return jsonify({"status": "Success", "title": title}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "Error", "message": str(e)}), 500


def regen_title_bard(resp):
    """
    Regenerates the title using the Bard model.

    Parameters:
    resp (str): The response to generate the title from.

    Returns:
    str: The regenerated title.
    """
    try:
        title = bard_client.generate_content(REGEN_TITLE + streaming_results["bard_title"] + resp).text
        
        print("regen title,", title)
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
    
    
######################################
###              META              ###
######################################
    
def process_meta(preconditional, prompt, streaming_results):
    """
    Processes the Meta model to generate a response.

    Parameters:
    preconditional (str): The precondition for the prompt.
    prompt (str): The user's prompt.
    streaming_results (dict): The dictionary to store the streaming results.

    Returns:
    None
    """
    try:
        meta_result = meta_client.prompt(message=preconditional + prompt + META_SPECIAL)['message']
        streaming_results["meta"] = meta_result
        val = streaming_results["meta"].split("\n")[0]
        start = 1
        if val[0:7] == "Subject":
            start = 0
            
        streaming_results["meta_title"] = str(streaming_results["meta"].split("\n")[start])
        streaming_results["meta"] = str("\n".join(streaming_results["meta"].split("\n")[start+1:]))
    except Exception as e:
        streaming_results["meta"] = f"Error: {e}"


@app.route('/api/meta-regen', methods=['POST'])
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
    global streaming_results
    try:
        streaming_results["meta"] = ""

        meta_thread = threading.Thread(target=process_meta, args=(last_data["precon"], last_data["prompt"], streaming_results))
        meta_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/api/meta-regen-title', methods=['POST'])
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
        data = request.get_json()
        gpt_title = data.get("gptTitle", "")
        gpt_response = data.get("gptResponse", "")
        
        if not gpt_response:
            raise ValueError("gptResponse is required")
        
        title = regen_title_meta(gpt_response)
        print("title: ", title)
        return jsonify({"status": "Success", "title": title}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "Error", "message": str(e)}), 500


def regen_title_meta(resp):
    """
    Regenerates the title using the Meta model.

    Parameters:
    resp (str): The response to generate the title from.

    Returns:
    str: The regenerated title.
    """
    try:
        title = meta_client.prompt(message=REGEN_TITLE + streaming_results["meta_title"] + resp)['message']
        
        print("regen title,", title)
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
    

######################################
###              MAIN              ###
######################################

@app.route('/api/prompt-submission', methods=['POST'])
def handle_prompt_submission():
    """
    Handles the prompt submission.

    Parameters:
    request_data (dict): The request data containing the prompt, role, notes, and keywords.

    Returns:
    Response: A JSON response indicating the status of the prompt submission.
    """
    global streaming_results
    request_data = request.get_json()
    precon = request_data.get('role') + "\n\n"
    prompt = request_data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    streaming_results = {"gpt": "", "bard": "", "meta": ""}
    
    notes = request_data.get('notes')
    keywords = request_data.get('keywords')
    if additional:
        precon += f"-- Additional info: {additional}"
    if notes:
        precon += f"-- Notes: {notes}"
    if keywords:
        precon += f"-- Keywords: {keywords}"
    precon += f"\n{PROMPT_INFO}"
    
    last_data["precon"] = precon
    last_data["prompt"] = prompt
    print([precon, prompt])

    gpt_thread = threading.Thread(target=process_gpt, args=(precon, prompt, streaming_results))
    bard_thread = threading.Thread(target=process_bard, args=(precon, prompt, streaming_results))
    meta_thread = threading.Thread(target=process_meta, args=(precon, prompt, streaming_results))
    
    gpt_thread.start()
    bard_thread.start()
    meta_thread.start()
    print(streaming_results)

    return jsonify({"status": "Processing"}), 200

@app.route('/api/stream-results/<model>', methods=['GET'])
def stream_results(model):
    """
    Streams the results of the prompt generation for a specific model.

    Parameters:
    model (str): The model for which the results need to be streamed.

    Returns:
    Response: A server-sent event response containing the title and content of the generated prompt.
    """
    def generate():
        while not streaming_results[model]:
            time.sleep(1)
        title = streaming_results[f"{model}_title"].replace('\n', '`')
        content = streaming_results[model].replace('\n', '`')
        s = f"data: {{\"title\": \"{title}\", \"content\": \"{content}\"}}\n\n"
        print(s)
        yield s

    return Response(generate(), mimetype='text/event-stream')



#######################################
###              OTHER              ###
#######################################
@app.route('/api/model-dropdown-selected', methods=['POST'])
def handle_model_dropdown_selected():
    """
    Handles the model dropdown selection event.

    Parameters:
    request_json (dict): The request data containing the selected model option.

    Returns:
    JSON response: A JSON response containing the selected model and a message indicating the selection.
    """
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')

    data['model'] = selected_option
    data['model_selection_message'] = f'Selected model: "{selected_option}"'

    return jsonify(data)


@app.route('/api/role-dropdown-selected', methods=['POST'])
def handle_role_dropdown_selected():
    """
    Handles the role dropdown selection event.

    Parameters:
    request_json (dict): The request data containing the selected role option.

    Returns:
    JSON response: A JSON response containing the selected role and the corresponding info.
    """
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown role "{selected_option}" has been selected.')

    data['role'] = selected_option
    data['info'] = ROLE_VALUES.get(selected_option)
    return jsonify(data)


@app.route('/api/selection-choice', methods=['POST'])
def handle_selection_choice():
    """
    Handles the selection choice event.

    Parameters:
    request_json (dict): The request data containing the selected option.

    Returns:
    JSON response: A JSON response containing the updated additional options.
    """
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')

    curr_val = str(selected_option).split()[0]
    for i in range(len(additional)):
        first_val = str(additional[i]).split()[0]
        if curr_val == first_val:
            additional.pop(i)
        
    additional.append(selected_option)
    return jsonify(data)



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
            app.run(debug=True)
        except Exception as e:
            print(f"Server error: {e}. Restarting in {retry_interval} seconds...")
            time.sleep(retry_interval)

def main(val):
    # if val:
    #     value = int(input("(1) One time server\n(2) Server with error handling\n> "))
    #     if value == 1:
            # app.run(debug=True)
    # app.run(debug=False)
    run_app_with_retries()

if __name__ == '__main__':
    main(True)
