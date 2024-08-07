from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    modules_telecommand = data.get('modulesTelecommand')
    keyspace = data.get('keyspace')
    contact_points = data.get('contact_points')
    cluster_port = data.get('clusterPort')
    asn_files = data.get('asn_files')

    # Guardar archivos ASN1 temporalmente
    file_paths = []
    for file in asn_files:
        file_path = f'/tmp/{file["filename"]}'
        with open(file_path, 'wb') as f:
            f.write(file['content'].encode('latin1'))
        file_paths.append(file_path)

    # Construir el comando
    command = [
        "python3", "/dmt/src/asn2dataModel.py",
        f"-modulesTelecommand", modules_telecommand,
        f"-keyspace", keyspace,
        f"-contact_points", contact_points,
        f"-clusterPort", cluster_port
    ] + file_paths

    # Ejecutar el comando
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout
    error = result.stderr

    # Limpiar archivos temporales
    for file_path in file_paths:
        os.remove(file_path)

    return jsonify({"output": output, "error": error})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
