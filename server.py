"""
Omkar Patel

This is an application that allows users to create sessions with different versions of AI models such as chatgpt, meta ai, and bard.
The user will select and input values in multiple textboxes and select menus which are passed through a generated prompt to the models. 
All of the different models' outputs are displayed at the same time so that comparison is easy.

Tech Stack: Python Flask API Backend, Reach JS with Tailwind, Chatgpt API, Bard API, Meta Ai API
--
Example Prompting:
Write an email introducing rysun as a consulting company on linkedin campaign.
Data, AI, Digital Transformation, CDM, CMMI Level 5 Certified

prof
concise
medium
moderate

--
Future Ideas:

1*. Fix bugs - None as of now, as they arise
2. Scoring Slider
3*. Add area for user to edit/create the prompt passed to models
4. Implement Ron
"""


from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv
from meta_ai_api import MetaAI
from flask_cors import CORS
from openai import OpenAI
import google.generativeai as genai
import os
import threading
import time

from constants import PROMPT_INFO, META_SPECIAL, DEFAULT_VALUES, ROLE_VALUES, PRECON, REGEN_TITLE

# Load environment variables
load_dotenv()
app = Flask(__name__)
CORS(app)

# Create a client for each model
chatgpt_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
genai.configure(api_key=os.environ["BARD_API_KEY"])
bard_client = genai.GenerativeModel('gemini-1.0-pro-latest')
meta_client = MetaAI()

# Information to use to pass into models
data = {'model': ''}  # Stores current model selection and status
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


# Status of API. Gets pinged every 5 seconds.
@app.route('/api/status', methods=['GET'])
def get_status():
    data['status'] = 'ok'
    return jsonify(data), 200

streaming_results = {"gpt": "", "bard": "", "meta": ""}

def process_gpt(preconditional, prompt, streaming_results):
    try:
        # preconditional_completion = chatgpt_client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     # model="gpt-4o",
        #     messages=[{"role": "system", "content": preconditional}]
        # )
        
        # precon_response = preconditional_completion.choices[0].message.content

        prompt_completion = chatgpt_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                # {"role": "system", "content": preconditional},
                # {"role": "assistant", "content": precon_response},
                {"role": "user", "content": preconditional+prompt}
            ]
        )
        print(prompt_completion.choices)
        print(preconditional, prompt)
        
        streaming_results["gpt"] = prompt_completion.choices[0].message.content
        streaming_results["gpt_title"] = str(streaming_results["gpt"].split("\n")[0])
        streaming_results["gpt"] = str("\n".join(streaming_results["gpt"].split("\n")[1:]))
        print("GPT result: ", streaming_results["gpt"])
        print(f"\n\nTitle: {streaming_results["gpt_title"]}\n\n")
    except Exception as e:
        streaming_results["gpt"] = f"Error: {e}"


def process_bard(preconditional, prompt, streaming_results):
    try:
        # bard_client.generate_content(preconditional)
        preconditional += prompt
        
        bard_result = bard_client.generate_content(preconditional).text
        
        streaming_results["bard"] = bard_result
        streaming_results["bard_title"] = str(streaming_results["bard"].split("\n")[0])
        streaming_results["bard"] = str("\n".join(streaming_results["bard"].split("\n")[1:]))
        
    except Exception as e:
        streaming_results["bard"] = f"Error: {e}"

def process_meta(preconditional, prompt, streaming_results):
    try:
        # meta_client.prompt(message=preconditional + META_SPECIAL)
        
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

@app.route('/api/gpt-regen', methods=['POST'])
def handle_gpt_regen():
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
        
@app.route('/api/bard-regen-title', methods=['POST'])
def handle_bard_regen_title():
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
        
@app.route('/api/meta-regen-title', methods=['POST'])
def handle_meta_regen_title():
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

def regen_title_gpt(resp):
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
    
def regen_title_bard(resp):
    try:
        title = bard_client.generate_content(REGEN_TITLE + streaming_results["bard_title"] + resp).text
        
        print("regen title,", title)
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e
    
def regen_title_meta(resp):
    try:
        title = meta_client.prompt(message=REGEN_TITLE + streaming_results["meta_title"] + resp)['message']
        
        print("regen title,", title)
        return title
    except Exception as e:
        print("Exception in regen_title:", str(e))
        raise e


@app.route('/api/bard-regen', methods=['POST'])
def handle_bard_regen():
    global streaming_results
    try:
        streaming_results["bard"] = ""

        bard_thread = threading.Thread(target=process_bard, args=(last_data["precon"], last_data["prompt"], streaming_results))
        bard_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    
@app.route('/api/meta-regen', methods=['POST'])
def handle_meta_regen():
    global streaming_results
    try:
        streaming_results["meta"] = ""

        meta_thread = threading.Thread(target=process_meta, args=(last_data["precon"], last_data["prompt"], streaming_results))
        meta_thread.start()
        
        return jsonify({"status": "Processing"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
    
@app.route('/api/prompt-submission', methods=['POST'])
def handle_prompt_submission():
    global streaming_results
    request_data = request.get_json()
    precon = request_data.get('role') + "\n\n"
    prompt = request_data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Reset streaming results
    streaming_results = {"gpt": "", "bard": "", "meta": ""}
    
    # Update the prompt with additional info, notes, and keywords if provided.
    notes = request_data.get('notes')
    keywords = request_data.get('keywords')
    if additional:
        precon += f"-- Additional info: {additional}"
    if notes:
        precon += f"-- Notes: {notes}"
    if keywords:
        precon += f"-- Keywords: {keywords}"
    precon += f"\n{PROMPT_INFO}"
    # precon += f"\n{PRECON}"
    
    last_data["precon"] = precon
    last_data["prompt"] = prompt
    print([precon, prompt])
    # Start threads for each model
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
    def generate():
        while not streaming_results[model]:
            time.sleep(1)
        title = streaming_results[f"{model}_title"].replace('\n', '`')
        content = streaming_results[model].replace('\n', '`')
        s = f"data: {{\"title\": \"{title}\", \"content\": \"{content}\"}}\n\n"
        print(s)
        yield s

    return Response(generate(), mimetype='text/event-stream')


# Handles logic for choosing a model
@app.route('/api/model-dropdown-selected', methods=['POST'])
def handle_model_dropdown_selected():
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')

    data['model'] = selected_option
    data['model_selection_message'] = f'Selected model: "{selected_option}"'

    return jsonify(data)

@app.route('/api/role-dropdown-selected', methods=['POST'])
def handle_role_dropdown_selected():
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown role "{selected_option}" has been selected.')

    data['role'] = selected_option
    data['info'] = ROLE_VALUES.get(selected_option)
    return jsonify(data)

# Handles logic for when a user selects options in the dropdown menu
@app.route('/api/selection-choice', methods=['POST'])
def handle_selection_choice():
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

# Run app in dev mode with error handling
def run_app_with_retries():
    retry_interval = 5
    while True:
        try:
            app.run(debug=True)
        except Exception as e:
            print(f"Server error: {e}. Restarting in {retry_interval} seconds...")
            time.sleep(retry_interval)

# Main function
def main(val):
    # if val:
    #     value = int(input("(1) One time server\n(2) Server with error handling\n> "))
    #     if value == 1:
            # app.run(debug=True)
    # app.run(debug=False)
    run_app_with_retries()

if __name__ == '__main__':
    main(True)
