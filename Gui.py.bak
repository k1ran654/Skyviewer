from flask import Flask, render_template, request
from app import api

gui = Flask(__name__)

@gui.route('/')
def index():
    return render_template('index.html')

@gui.route('/stats', methods=['POST'])
def get_stats():
    username = request.form.get('username')
    if not username:
        return "Please enter a username", 400

    data = api.get_player_data(username)
    if not data:
        return f"Could not fetch data for {username}", 404

    return render_template('index.html', **data)

if __name__ == '__main__':
    gui.run(host='0.0.0.0', port=8080, debug=True)
