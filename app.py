from flask import Flask, jsonify, request
from dotenv import load_dotenv
from meta_ai_api import MetaAI
from flask_cors import CORS
from openai import OpenAI
from bardapi import Bard
import time, os

load_dotenv()
app = Flask(__name__)

chatgpt_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
# gemini_client = Bard(
    # token=os.environ.get("BARD_API_KEY")
# )
meta_client = MetaAI()

CORS(app)

current_model = ""
data = {'model': current_model}

@app.route('/api/status', methods=['GET']) ## status of api. gets pinged every 5s
def get_status():
    data['status'] = 'ok'
    return jsonify(data), 200

@app.route('/api/prompt-submission', methods=['POST']) ## handles when a user submits a prompt, no matter which ai they choose
def handle_prompt_submission():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model')
    result = ''
    print(model)

    print(f"Prompt received: {prompt}")

    if not model:
        result = "Please select a model"
        
    elif model == "ChatGPT":
        try:
            completion = chatgpt_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                ]
            )

            result = completion.choices[0].message.content
            print(result)
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": str(e)}), 500
        
    # elif model == "Bard":
    #     try:
            # completion = gemini_client.generate_content(prompt)
            # result = completion.payload
    #         print(result)
            
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         return jsonify({"error": str(e)}), 500
        
    elif model == "Meta AI":
        try:
            result = meta_client.prompt(message=prompt)['message']
            print(result)
            
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": str(e)}), 500

    else:
        result = "Current model not supported"

    output = {"response": result, "prompt": prompt}
    return jsonify(output)


@app.route('/api/model-dropdown-selected', methods=['POST'])
def handle_model_dropdown_selected():
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')

    print(data['model'])
    data['model_selection_message'] = f'Selected model: "{data['model']}"'

    data['model'] = selected_option
    # if selected_option not in data['model']:
        # data['model'].append(selected_option)
    # else:
        # data['model'].remove(selected_option)

    return jsonify(data)

def run_app_with_retries():
    retry_interval = 5
    while True:
        try:
            app.run(debug=True)
        except Exception as e:
            print(f"Server error: {e}. Restarting in {retry_interval} seconds...")
            time.sleep(retry_interval)

run_app_with_retries()