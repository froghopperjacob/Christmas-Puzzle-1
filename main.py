import flask
import random
import logging
from flask_socketio import SocketIO, emit

app = flask.Flask(__name__)
app.config.from_object(__name__)

socketio = SocketIO(app)

challenge = 1
battle = 1

battle1PingPong = 0
battle1Smash = 0
battle1Tennis = 0

battle2PingPong = 0
battle2Smash = 0
battle2Tennis = 0

currentSolutionWins = 4

pSolution = "345456487"

players = []
solutionsFinished = []

def grouped(iterable, n):
	return zip(*[iter(iterable)]*n)

# Pictures
@app.route('/favicon.ico')
def favicon():
    return flask.current_app.send_static_file('favicon.ico')

@app.route('/background.jpg')
def background():
    return flask.current_app.send_static_file('background.jpg')

# APIS
@app.route('/reset')
def reset():
	socketio.emit('server_reset', broadcast=True)

	return flask.redirect('/')

@app.route('/edit')
def edit():
	name = flask.request.args.get('name')
	newWins = flask.request.args.get('wins')

	for player in players:
		if player['name'] == name:
			player['wins'] = player['wins'] + int(newWins)

	socketio.emit('server_player_change', players, broadcast=True)

	return flask.redirect('/')

@app.route('/final')
def final():
	global currentSolutionWins

	for data in solutionsFinished:
		for player in players:
			if data['name'] == player['name']:
				player['wins'] = player['wins'] + currentSolutionWins

				currentSolutionWins = currentSolutionWins - 1

	socketio.emit('server_player_change', players, broadcast=True)

	return flask.redirect('/')

@app.route('/ichallenge')
def ichallenge():
	global challenge

	if challenge == 1:
		shuffledPlayers = players.copy()
		challenges = []

		random.shuffle(shuffledPlayers)

		for player in players:
			challenges.append({
				'name': player['name'],

				'challenge': shuffledPlayers.pop(0)['challenge1']
			})
		
		socketio.emit('server_challenge', challenges, broadcast=True)

		challenge = 2
	else:
		shuffledPlayers = players.copy()
		challenges = []

		random.shuffle(shuffledPlayers)

		for player in players:
			challenges.append({
				'name': player['name'],

				'challenge': shuffledPlayers.pop(0)['challenge2']
			})
		
		socketio.emit('server_challenge', challenges, broadcast=True)

	return flask.redirect('/') 

@app.route('/ibattle')
def ibattle():
	global battle

	if battle == 1:
		shuffledPlayers = players.copy()
		battles = []

		random.shuffle(shuffledPlayers)
		
		battle1 = "Ping Pong" if battle1PingPong >= battle1Smash + battle1Tennis else "Super Smash" if battle1Smash >= battle1PingPong + battle1Tennis else "Tennis Aces"

		for player1, player2 in grouped(shuffledPlayers, 2):
			battles.append({
				'name1': player1['name'],
				'name2': player2['name'],

				'battle': battle1
			})
		
		socketio.emit('server_battle', battles, broadcast=True)
	else:
		shuffledPlayers = players.copy()
		battles = []

		battle2 = "Ping Pong" if battle2PingPong >= battle2Smash + battle2Tennis else "Super Smash" if battle2Smash >= battle2PingPong + battle2Tennis else "Tennis Aces"

		random.shuffle(shuffledPlayers)

		for player1, player2 in grouped(shuffledPlayers, 2):
			battles.append({
				'name1': player1['name'],
				'name2': player2['name'],

				'battle': battle2
			})
		
		socketio.emit('server_battle', battles, broadcast=True)

	return flask.redirect('/')

# Sockets
@socketio.on('connect')
def connect():
	print('Client connected')

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

@socketio.on('client_solution')
def solution(data):
	solutionsFinished.append(data)

@socketio.on('client_info')
def info(data):
	players.append(data)

	emit('server_player_change', players, broadcast=True)

@socketio.on('client_check_finished')
def checkFinished(name):
	isPlayer = False

	for player in players:
		if player['name'] == name:
			isPlayer = True

	socketio.emit('client_check_finished_callback', {"name": name, "success": isPlayer})

	if isPlayer:
		socketio.emit('server_player_change', players, broadcast=True)

@socketio.on('client_check')
def check(name, gSolution):
	emit('client_check_callback', {"name": name, "success": gSolution == pSolution})

# HTML
@app.route('/scoreboard')
def scoreboard():
	return flask.render_template('scoreboard.html', players=players)

@app.route('/')
def index():
	return flask.current_app.send_static_file('index.html')

if __name__ == "__main__":
	app.debug = True
	app.run(host='0.0.0.0', port=80)