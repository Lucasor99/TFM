from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)
app.config['DEBUG'] = True

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

    csv_files = request.files.getlist('csv_file')


    # Procesar cada archivo CSV
    for csv_file in csv_files:
        # Guardar el archivo CSV temporalmente
        csv_filename = os.path.join('filesCSV', csv_file.filename)
        csv_file.save(csv_filename)

    # Construir el comando
    command = [
        "python3",
        "/dmt/src/ReadWriteTMTC/readTMTC.py",
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
    print(command)
    print(output)
    print(error)

    # Limpiar archivos temporales
    for filename in csv_files:
        os.remove(os.path.join('filesASN1', filename))

    return jsonify({"command": command, "output": output, "error": error})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
