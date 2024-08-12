from flask import Flask, request, jsonify, send_from_directory, after_this_request
import subprocess
import os

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/create_models', methods=['POST'])
def process():
    # Obtener los datos de la solicitud POST
    modules_telecommand = request.form.get('modulesTelecommand', '')
    keyspace = request.form.get('keyspace', '')
    contact_points = request.form.get('contact_points', '')
    cluster_port = request.form.get('clusterPort', '')

    asn_files = request.files.getlist('asn_files')

    # Guardar archivos ASN1 temporalmente y recolectar los nombres de archivos
    filenames = []
    for file in asn_files:
        file_path = os.path.join('filesASN1', file.filename)
        file.save(file_path)
        filenames.append(file.filename)

    # Construir el comando
    command = ["python3", "src/asn2dataModel.py"]

    if modules_telecommand:
        command.extend([f"-modulesTelecommand", modules_telecommand])

    if keyspace:
        command.extend([f"-keyspace", keyspace])

    if contact_points:
        command.extend([f"-contact_points", contact_points])

    if cluster_port:
        command.extend([f"-clusterPort", cluster_port])

    command.append('./filesASN1')  
    command.extend(filenames) 

    # Ejecutar el comando
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout
    error = result.stderr

    # Limpiar archivos temporales
    for filename in filenames:
        os.remove(os.path.join('filesASN1', filename))

    return jsonify({"command": command, "output": output, "error": error})


@app.route('/read_tmtc', methods=['POST'])
def process_csv():

    keyspace = request.form.get('keyspace', '')
    contact_points = request.form.get('contact_points', '')
    cluster_port = request.form.get('clusterPort', '')

    csv_files = request.files.getlist('csv_files')

    if os.path.exists(os.path.join('filesCSV', 'zzz.txt')):
        os.remove(os.path.join('filesCSV', 'zzz.txt'))

    # Procesar cada archivo CSV
    csv_filenames = []
    for csv_file in csv_files:
        # Guardar el archivo CSV temporalmente
        csv_filename = os.path.join('filesCSV', csv_file.filename)
        csv_file.save(csv_filename)
        csv_filenames.append(csv_file.filename)

    # Construir el comando
    command = [
        "python3",
        "src/ReadWriteTMTC/readCSV.py",
        "./filesCSV"
    ]

    if keyspace:
        command.extend([f"-keyspace", keyspace])

    if contact_points:
        command.extend([f"-contact_points", contact_points])

    if cluster_port:
        command.extend([f"-clusterPort", cluster_port])

    # Ejecutar el comando
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout
    error = result.stderr

    # Limpiar archivos temporales
    for filename in csv_filenames:
        os.remove(os.path.join('filesCSV', filename))

    return jsonify({"command": command, "output": output, "error": error})


@app.route('/createCSV', methods=['POST'])
def create_csv():
    # Obtener los datos de la solicitud POST
    keyspace = request.form.get('keyspace', '')
    contact_points = request.form.get('contact_points', '')
    cluster_port = request.form.get('clusterPort', '')
    send_telecommands = request.form.get('sendTelecommands', '')
    
    tablenames = request.form.get('tablenames', '').split(' ')
    print(tablenames)

    # Construir el comando
    command = [
        "python3",
        "src/ReadWriteTMTC/createCSV.py",
        "./filesTelecommand"
    ]
    for tablename in tablenames:
        command.extend([ tablename])
        
    command.extend([f"-keyspace", keyspace])
    command.extend([f"-contact_points", contact_points])
    command.extend([f"-clusterPort", cluster_port])

    if send_telecommands:
        command.extend([f"-sendTelecommands", send_telecommands])

    # Ejecutar el comando
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout
    error = result.stderr

    # Verificar y devolver los archivos CSV generados
    csv_files = []
    for filename in os.listdir('filesTelecommand'):
        if filename.endswith('.csv'):
            csv_files.append(filename)
           

    # Crear respuesta JSON con archivos CSV generados
    files_info = [{"filename": f, "url": f"/filesTelecommand/{f}"} for f in csv_files]
 

    return jsonify({"command": command, "output": output, "error": error, "files": files_info})

@app.route('/filesTelecommand/<filename>')
def download_file(filename):
    file_path = os.path.join('filesTelecommand', filename)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
        except Exception as e:
            app.logger.error(f'Error removing file {file_path}: {e}')
        return response

    return send_from_directory('filesTelecommand', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
