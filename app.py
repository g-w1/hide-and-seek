import os
import pickle
import random
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = 'users.pickle'
db_lock = threading.Lock()

def load_users():
    with db_lock:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as f:
                return pickle.load(f)
        return {}

def save_users(users):
    with db_lock:
        with open(DB_FILE, 'wb') as f:
            pickle.dump(users, f)

@app.route('/', methods=['POST'])
def register_or_update_user():
    data = request.json
    users = load_users()
    
    user = data.get('user')
    lat = data.get('lat')
    long = data.get('long')
    print(data)
    
    if not all([user, lat, long]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if user in users:
        users[user]['lat'] = lat
        users[user]['long'] = long
    else:
        users[user] = {
            'type': 'NOTSTARTED',
            'lat': lat,
            'long': long
        }
    
    save_users(users)
    
    return jsonify({"type": users[user]['type']})

@app.route('/', methods=['GET'])
def get_users():
    users = load_users()
    if not users:
        return jsonify({"error": "No users found"}), 404
    
    result = []
    for user, data in users.items():
        user_type = data['type']
        if user_type == 'HUNTER':
            result.append({
                "user": user,
                "type": user_type,
                "lat": data['lat'],
                "long": data['long']
            })
        elif user_type == 'SPEEDRUNNER':
            rounded_lat, rounded_long = data['lat'], data['long']
            result.append({
                "user": user,
                "type": user_type,
                "lat": rounded_lat,
                "long": rounded_long
            })
        else:  # NOTSTARTED
            result.append({
                "user": user,
                "type": user_type
            })
    
    return jsonify(result)

@app.route('/start', methods=['POST'])
def start_game():
    users = load_users()
    if len(users) < 4:
        return jsonify({"error": "Not enough users to start the game"}), 400
    
    user_list = list(users.keys())
    random.shuffle(user_list)
    
    for i, user in enumerate(user_list):
        if i < 3:
            users[user]['type'] = 'HUNTER'
        else:
            users[user]['type'] = 'SPEEDRUNNER'
    
    save_users(users)
    
    return jsonify({"message": "Game started", "hunters": user_list[:3], "speedrunners": user_list[3:]})

@app.route('/page/', methods=['GET'])
def page():
    return app.send_static_file('index.html')

@app.route('/page/<path:path>', methods=['GET'])
def page_path(path):
    return app.send_static_file(path)

if __name__ == '__main__':
    app.run(debug=True)