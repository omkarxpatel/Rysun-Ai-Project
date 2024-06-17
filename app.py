from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS from flask_cors

app = Flask(__name__)
CORS(app)  # Enable CORS for your Flask app

@app.route('/api/data', methods=['GET'])
def get_data():
    data = {"message": "Hello from the backend!"}
    return jsonify(data)

@app.route('/api/button-clicked', methods=['POST'])
def handle_button_click():
    button_data = request.json
    button_name = button_data.get('buttonName')
    print(f'Button "{button_name}" has been clicked.')
    return jsonify({'message': f'Handled button click for "{button_name}"'})

@app.route('/api/dropdown-selected', methods=['POST'])
def handle_dropdown_selected():
    selected_data = request.json
    selected_option = selected_data.get('selectedOption')
    print(f'Dropdown option "{selected_option}" has been selected.')
    return jsonify({'message': f'Selected option "{selected_option}"'})

if __name__ == '__main__':
    app.run(debug=True)
