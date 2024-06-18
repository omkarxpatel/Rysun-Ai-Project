from flask import Flask, jsonify, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

## GLOBAL VALUES

current_models = [] 
data = {'models':current_models}
# array because multiple can be used at once
# in case with more than 1 model, use chatgpt to summarize all outputs or just display all at once

@app.route('/api/data', methods=['GET'])
def get_data():
    data["message"] = "Hello"
    return jsonify(data)


@app.route('/api/button-clicked', methods=['POST'])
def handle_button_click():
    button_data = request.json
    button_name = button_data.get('buttonName')
    print(f'Button "{button_name}" has been clicked.')

    data['message'] = f'Handled button click for "{button_name}"'
    return jsonify(data)


"""
Used for the AI model selection

gathers inputs and adds the users models to an array; current_models
"""
@app.route('/api/dropdown-selected', methods=['POST'])
def handle_model_dropdown_selected():
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')
    
    print(data['models'])
    data['model_selection_message'] = f'Selected models: "{data['models']}"'

    if selected_option not in data['models']:
        data['models'].append(selected_option)
    else:
        data['models'].remove(selected_option)

    return jsonify(data)



def run_app_with_retries():
    retry_interval = 5
    while True:
        try:
            app.run(debug=True)
        except Exception as e:
            print(f"Server error: {e}. Restarting in {retry_interval} seconds...")
            time.sleep(retry_interval)
            

if __name__ == '__main__':
    # app.run(debug=True)
    run_app_with_retries()
