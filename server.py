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

from constants import PROMPT_INFO, META_SPECIAL, DEFAULT_VALUES

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


# Status of API. Gets pinged every 5 seconds.
@app.route('/api/status', methods=['GET'])
def get_status():
    data['status'] = 'ok'
    return jsonify(data), 200

streaming_results = {"gpt": "", "bard": "", "meta": ""}

def process_gpt(prompt, streaming_results):
    try:
        completion = chatgpt_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        streaming_results["gpt"] = completion.choices[0].message.content
        print(streaming_results)
    except Exception as e:
        streaming_results["gpt"] = f"Error: {e}"

def process_bard(prompt, streaming_results):
    try:
        bard_result = bard_client.generate_content(prompt).text
        streaming_results["bard"] = bard_result
    except Exception as e:
        streaming_results["bard"] = f"Error: {e}"

def process_meta(prompt, streaming_results):
    try:
        meta_result = meta_client.prompt(message=prompt + META_SPECIAL)['message']
        streaming_results["meta"] = meta_result
    except Exception as e:
        streaming_results["meta"] = f"Error: {e}"

@app.route('/api/prompt-submission', methods=['POST'])
def handle_prompt_submission():
    global streaming_results
    request_data = request.get_json()
    prompt = request_data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Reset streaming results
    streaming_results = {"gpt": "", "bard": "", "meta": ""}
    
    # Update the prompt with additional info, notes, and keywords if provided.
    notes = request_data.get('notes')
    keywords = request_data.get('keywords')
    if additional:
        prompt += f"-- Additional info: {additional}"
    if notes:
        prompt += f"-- Notes: {notes}"
    if keywords:
        prompt += f"-- Keywords: {keywords}"
    prompt += f"\n{PROMPT_INFO}"
    
    # Start threads for each model
    gpt_thread = threading.Thread(target=process_gpt, args=(prompt, streaming_results))
    bard_thread = threading.Thread(target=process_bard, args=(prompt, streaming_results))
    meta_thread = threading.Thread(target=process_meta, args=(prompt, streaming_results))
    
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
        s = f"data: {streaming_results[model].replace('\n', '`')}\n\n"
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
    if val:
        value = int(input("(1) One time server\n(2) Server with error handling\n> "))
        if value == 1:
            app.run(debug=True)
    app.run(debug=False)

if __name__ == '__main__':
    main(False)
