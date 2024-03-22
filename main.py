from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import time
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=None)

# Game state
game_state = {
    'players': {},  # Tracks players by unique ID
    'ball': {'x': 300, 'y': 200, 'vx': 5, 'vy': 5}
}

def game_thread():
    paddle_width = 10  # Assuming each paddle is 10 pixels wide
    paddle_height = 50  # Assuming each paddle is 50 pixels tall
    ball_size = 10  # Assuming the ball is 10x10 pixels

    while True:
        # Move the ball
        game_state['ball']['x'] += game_state['ball']['vx']
        game_state['ball']['y'] += game_state['ball']['vy']
        
        # Check for collisions with the top and bottom walls
        if game_state['ball']['y'] <= 0 or game_state['ball']['y'] + ball_size >= 400:
            game_state['ball']['vy'] *= -1

        # Check for collisions with paddles
        for player_id, player in game_state['players'].items():
            paddle_x = player['x']
            paddle_y = player['y']
            
            # Check if the ball's current position overlaps with the paddle's position
            if paddle_x < game_state['ball']['x'] + ball_size and paddle_x + paddle_width > game_state['ball']['x']:
                if paddle_y < game_state['ball']['y'] + ball_size and paddle_y + paddle_height > game_state['ball']['y']:
                    # Collision detected, reverse the ball's x velocity
                    game_state['ball']['vx'] *= -1
                    break  # No need to check other paddles

        # Emit the updated game state to all connected clients
        socketio.emit('game_state', game_state)
        time.sleep(0.01)


@app.route('/')
def index():
    return render_template('index.html', title='Pong Game', domain='localhost', port='5000', canvas_width=600, canvas_height=400)

@socketio.on('connect')
def handle_connect():
    new_player_id = str(uuid.uuid4())
    player_x_position = 50 if len(game_state['players']) % 2 == 0 else 550
    game_state['players'][new_player_id] = {'x': player_x_position, 'y': 100}
    print(f'Client connected: {new_player_id}')
    # Emit the player ID to only the connecting client
    socketio.emit('player_id', {'id': new_player_id}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    # Implement player disconnection logic here
    print('Client disconnected')

@socketio.on('game_action')
def handle_game_action(data):
    player_id = data.get('id')
    action = data.get('move')
    if player_id in game_state['players']:
        if action == 'up':
            game_state['players'][player_id]['y'] -= 10
        elif action == 'down':
            game_state['players'][player_id]['y'] += 10
        print(f'Action received from {player_id}: {action}')

if __name__ == '__main__':
    threading.Thread(target=game_thread, daemon=True).start()
    socketio.run(app, debug=True)
