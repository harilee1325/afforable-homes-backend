
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
import datetime


app = Flask(__name__)

# Application Default credentials are automatically created.
cred = credentials.Certificate('affordable-key.json')
default_app = initialize_app(cred)

db = firestore.client()


db = firestore.client()
todo_ref = db.collection('todos')

@app.route('/add', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON.
        todo : Return document that matches query ID.
        all_todos : Return all documents.
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')
        if todo_id:
            todo = todo_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        todo_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"



bookings = db.collection('bookings')
rooms = db.collection('rooms')


@app.route('/rooms', methods=['GET'])
def rooms_list():
    """
        read() : returns all the room details
    """
    try:
        room = [doc.to_dict() for doc in rooms.stream()]
        return jsonify(room), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/create_booking', methods=['POST'])
def create_booking():
    """
        create_booking() : Used to create a booking for the set of rooms
        e.g. json={'no': '1', 'type': 'cleaning', 'date' : 'date', 'status': 0/1}
        1 - active
        0 - no booking
    """
    try:
        room_no = request.json['no']
        booking_type = request.json['type']
        room = rooms.where(u'room_no', u'==', room_no).where(u'status', u'==', 1).get()

        for doc in room:
             print(f'{doc.id} => {doc.to_dict()}')
        if (len(room)>0):
            return jsonify({"success": False, "message" : "Room already booked"}), 403
        else:
            bookings.add(request.json)
            room_update = rooms.where(u'room_no', u'==', room_no).where(u'status', u'==', 0).get()
            for doc_ref in room_update:
                # Document Reference
                doc = rooms.document(doc_ref.id)
                doc.update({u"booking_type": booking_type})
                doc.update({u"status": request.json['status']})
            return jsonify({"success": True, "message" : "booking created"}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"




@app.route('/room_stat', methods=['POST', 'PUT'])
def update_room_stat():
    """
        update_room_stat() : update the status of room from the sensor input
        e.g. json={'no': '1', 'status': 0/1}
    """
    try:
        room_no = request.json['no']
        status = request.json['status']

        docs = rooms.where(u'room_no', u'==', room_no).get()[0]

        room_dict = docs.to_dict()
        if (room_dict['booking_type'] == "cleaning" or room_dict['booking_type'] == "stay" ):
            return jsonify({"success": True, "message": "Booking exists"}), 200
        else:
            sendNotification(room_no, status)
            return jsonify({"success": False, "message": "Room is opened without any active booking"}), 403
    except Exception as e:
        return f"An Error Occurred: {e}"



room_open = db.collection('room_open')

def sendNotification(room_no, status):
    print("send notification")
    current_time = datetime.datetime.now()
    data = {
        u'room_no': room_no,
        u'status': status,
        u'date': current_time
    }
    room_open.add(data)

port = int(os.environ.get('PORT', 8080))

if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)
    