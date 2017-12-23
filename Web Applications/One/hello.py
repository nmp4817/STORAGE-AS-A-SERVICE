from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify, make_response
import atexit
import cf_deployment_tracker
import os
import json
from base64 import b64encode

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('PORT', 8080))

@app.route('/')
def home():
    # return app.send_static_file('index.html')
    # return app.send_static_file('index.html')
    return render_template('index.html')

"""/* Endpoint to greet and add a new visitor to database.
* Send a POST request to localhost:8080/api/visitors with body
* {
* 	"name": "Bob"
* }
*/"""

def count_zeros(f):
    bytes = (ord(b) for b in f.read())
    for b in bytes:
        for i in xrange(8):
            yield (b >> i) & 1

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file_name = file.filename
    zero_counts = 0

    for b in count_zeros(file):
        if b == 0:    
            zero_counts += 1

    uploaded_file_content = b64encode(file.read())

    data = {'file_name': file_name,'zero_counts':zero_counts, '_attachments': {file_name : {'data': uploaded_file_content}}}
    doc = db.create_document(data)
    
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    file_name = request.form['filename']
    for document in db:
        if (document['file_name'] == file_name):
            file = document.get_attachment(file_name, attachment_type='binary')
            response = make_response(file)
            response.headers["Content-Disposition"] = "attachment; filename=%s"%file_name
            return response
        else:
            response = 'File not found'
    return response

@app.route('/delete', methods=['POST'])
def delete():
    file_name = request.form['filename']
    for document in db:
        if document['file_name'] == file_name:
            print("File found and deleted")
            document.delete()
            #document.delete_attachment(file_name)
        else:
            print ('File not found')
    return render_template('index.html')

@app.route('/list_files', methods=['POST'])
def list_files():
    return jsonify(list(map(lambda doc: [doc['file_name'],doc['zero_counts']], db)))
    # file_name = request.form['filename']
    # for document in db:
    #     if document['file_name'] == file_name:
    #         print("File found and deleted")
    #         document.delete()
    #         #document.delete_attachment(file_name)
    #     else:
    #         print ('File not found')
    # return render_template('index.html')


# @app.route('/api/visitors', methods=['GET'])
# def get_visitor():
#     if client:
#         return jsonify(list(map(lambda doc: doc['name'], db)))
#     else:
#         print('No database')
#         return jsonify([])

"""/**
 * Endpoint to get a JSON array of all the visitors in the database
 * REST API example:
 * <code>
 * GET http://localhost:8080/api/visitors
 * </code>
 *
 * Response:
 * [ "Bob", "Jane" ]
 * @return An array of all the visitor names
 */"""

# @app.route('/api/visitors', methods=['POST'])
# def put_visitor():
#     user = request.json['name']
#     if client:
#         data = {'name':request.json['name']}
#         db.create_document(data)
#         return 'Hello %s! I added you to the database.' % user
#     else:
#         print('No database')
#         return 'Hello %s!' % user

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
