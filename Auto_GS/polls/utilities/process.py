import requests
from django.shortcuts import render
from django.http import JsonResponse

def process_data(request):
    if request.method == 'POST':
        modules_telecommand = request.POST.get('modulesTelecommand')
        keyspace = request.POST.get('keyspace')
        contact_points = request.POST.get('contact_points')
        cluster_port = request.POST.get('clusterPort')
        asn_files = request.FILES.getlist('asn_files')

        # Preparar los datos y archivos para enviar a la API Flask
        files = [('asn_files', (file.name, file.read(), file.content_type)) for file in asn_files]
        data = {
            'modulesTelecommand': modules_telecommand,
            'keyspace': keyspace,
            'contact_points': contact_points,
            'clusterPort': cluster_port
        }

        response = requests.post('http://asn1scc-service:5000/process', files=files, data=data)

        return JsonResponse(response.json())

    return render(request, 'process_form.html')
