from flask import Flask, render_template, redirect, url_for, session, request
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Initialize the app
app = Flask(__name__)
# Set up a secret key
app.config["SECRET_KEY"] = "I am a serious dev"
# initialize socket integration
socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template("index.html")

# Store all the room data 
rooms = {}

# Generate code 
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break
    
    return code

@app.route("/join", methods=['GET', 'POST'])
def join():
    # Clear any previous running sessions
    session.clear()

    if request.method == 'POST':
        # Get the data
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False) # Opt to return False if the user did not click the join button
        create = request.form.get('create', False)

        # Check if the user had entered his or her name
        if not name:
            return render_template("join.html", error="Please Enter A Name!", code=code)
        
        # If the user has clicked join, check if he has entered the code
        if join != False and not code:
            return render_template("join.html", error="Please Enter the Code!", name=name)
        
        # If the user has the correct code, set the room and if the user creates a room, generate a unique code
        room = code
        if create != False:
            room = generate_unique_code(4)

            # Set the initial room data
            rooms[room] = {"members": 0,
                        "messages": []}
        elif code not in rooms:
            return render_template("join.html", error="Room Does Not Exist", name=name)
        
        # Create a session which is a semi permanent way of storing data
        session['room'] = room
        session['name'] = name

        # Redirect the user to the chat room
        return redirect(url_for("room"))


    return render_template("join.html")

@app.route("/room")
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('room'))
    
    return render_template("room.html", code=room, messages=rooms[room]['messages'])

# socket connection when user joins room
@socketio.on("connect")
def connect(auth):
    room = session.get('room')
    name = session.get('name')

    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": " has entered the room"}, to=room)
    rooms[room]['members'] += 1

# Leaving the room
@socketio.on("disconnect")
def disconnect():
    room = session.get('room')
    name = session.get('name')
    leave_room(room)
    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0:
            del rooms[room]
    send({"name": name, "message": " has left the room"}, to=room)

#The server receives the message and transmits to others
@socketio.on("message")
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    content = {
        "name" : session.get("name"),
        "message": data['data']
    }
    send(content, to=room)
    rooms[room]['messages'].append(content)
    
    
if __name__ == "__main__":
    socketio.run(app, debug=True)