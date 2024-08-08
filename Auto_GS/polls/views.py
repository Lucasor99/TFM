from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import redirect
from django.utils.translation import activate
from django.conf import settings
import requests.exceptions

from Auto_GS.cassandra_conection import get_cassandra_session
from .models import *

from .utilities.functions import insert_data, create_tree_view, select_by, update_data, delete_data

import json, random, requests



session = get_cassandra_session()

def change_language(request):
    lang_code = request.GET.get('language', settings.LANGUAGE_CODE)
    activate(lang_code)
    response = redirect(request.META.get('HTTP_REFERER', '/'))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response

@login_required
def index(request):

    try:
        select_query = "describe tables"
        result = session.execute(select_query)

        print(result.current_rows)

        columns = result.column_names
        rows = result.all()

        data = {
            'columnNames': columns,
            'rowData': [dict(zip(columns, row)) for row in rows]
        }

        # Renderiza la plantilla con los datos JSON
        return render(request, "index.html", {'data': data})

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")
        # Maneja el error adecuadamente, puedes regresar un JsonResponse si lo prefieres
        return render(request, "error.html", {'error_message': 'Error en la consulta a la base de datos.'})

@login_required
def tabla(request, item=None):
    try:
        print("Valor de item:", item)  # Imprimir el valor de item para depurar

        if item:
            # Realizar la consulta a Cassandra
            select_query = "SELECT * FROM {}".format(item)
        else:
            # Si no se proporciona el parámetro 'item', utilizar un valor predeterminado
            select_query = "SELECT * FROM example_dataview"

        result = session.execute(select_query)
        
        first_column_index = 0
        # Procesar los resultados
        columns = result.column_names
        rows = sorted(result.all(), key=lambda row: row[first_column_index])  # Ordenar por la primera columna

        data = {
            'columnNames': columns,
            'rowData': [dict(zip(columns, row)) for row in rows]
        }

        if len(data['rowData']) > 5:
            random_rows = random.sample(data['rowData'], 5)
        else:
            random_rows = data['rowData']

        busqueda_realizada = False

        if 'columna' in request.GET and 'valor' in request.GET:
            columna = request.GET['columna']
            print(columna)
            try:
                valor = int(request.GET['valor'])
                print(valor)
            except ValueError:
                valor = None

            # Verificar si hay un valor proporcionado
            if valor is not None:
                resultados = select_by(item, columna, valor)
                data['rowData'] = [dict(zip(columns, row)) for row in resultados]
                busqueda_realizada = True

        tree_data = json.dumps(create_tree_view(columns, item))

        # Renderiza la plantilla con los datos JSON
        return render(request, "tabla.html", {'data': data, 'tree_data': tree_data, 'item': item,'random_rows': random_rows, 'busqueda_realizada': busqueda_realizada})

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")
        # Maneja el error adecuadamente, puedes regresar un JsonResponse si lo prefieres
        return render(request, "error.html", {'error_message': 'Error en la consulta a la base de datos.'})


@login_required
@staff_member_required
def telecomando(request):
    success_message = "Los datos se han enviado correctamente a la base de datos."
    error_message = "Ha ocurrido un error, compruebe que ha introducido los datos correctamente"


    try:
        # Realizar la consulta a Cassandra
        select_query = "SELECT * FROM example_dataview"
        result = session.execute(select_query)

        # Procesar los resultados
        columns = result.column_names
        rows = result.all()

        data = {
            'columnNames': columns,
            'rowData': [dict(zip(columns, row)) for row in rows]
        }

        if request.method == 'POST':
            form = tcForm(request.POST)
            if form.is_valid():
                insert_data(form.cleaned_data)
                print(f"Los datos son válidos y se ha enviado a la DB")
                return render(request, "telecomando.html", {'data': data, 'success_message': success_message})
            else:
                print(f"No son validos los datos")
                return render(request, "telecomando.html", {'data': data,'form': form, 'error_message': error_message})
        else :
            form = tcForm()
            return render(request, "telecomando.html", {'data': data})

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")
        # Maneja el error adecuadamente, puedes regresar un JsonResponse si lo prefieres
        return render(request, "error.html", {'error_message': 'Error en la consulta a la base de datos.'})


@login_required
@staff_member_required
def update(request):
 # Imprimir el valor de item para depurar
    return render(request, "update.html")


@login_required
@staff_member_required
def modificar_tabla(request):
    if 'tabla' in request.GET:
        tabla_seleccionada = request.GET['tabla']

        select_query = "SELECT column_name FROM system_schema.columns WHERE keyspace_name = 'tfm' AND table_name = '{}';".format(tabla_seleccionada)
        result = session.execute(select_query)
        columns = [row.column_name for row in result]

        if request.method == 'POST':
            column = request.POST['column']
            new_column = request.POST['new_column']
            try:
                value = int(request.POST['value'])
                new_value = int(request.POST['new_value'])
            except ValueError:
                # Maneja el caso en el que los valores no puedan ser convertidos a enteros
                return HttpResponse("Los valores no son correctos")

            update_data(tabla_seleccionada,column,value,new_column,new_value)


        
        return render(request, 'modificar_tabla.html', {'tabla_seleccionada': tabla_seleccionada, "columns" :columns})
    else:
        # Manejar el caso donde no se seleccionó ninguna tabla
        return HttpResponse("No se seleccionó ninguna tabla.")


@login_required
@staff_member_required
def delete(request):
 # Imprimir el valor de item para depurar
    return render(request, "delete.html")

@login_required
@staff_member_required
def borrar_datos(request):
    if 'tabla' in request.GET:
        tabla_seleccionada = request.GET['tabla']

        select_query = "SELECT column_name FROM system_schema.columns WHERE keyspace_name = 'tfm' AND table_name = '{}';".format(tabla_seleccionada)
        result = session.execute(select_query)
        columns = [row.column_name for row in result]

        if request.method == 'POST':
            column = request.POST['column']
            try:
                value = int(request.POST['value'])
            except ValueError:
                # Maneja el caso en el que los valores no puedan ser convertidos a enteros
                return HttpResponse("Los valores no son correctos")
        
            delete_data(tabla_seleccionada, column, value)
        
        return render(request, 'borrar_datos.html', { 'tabla_seleccionada': tabla_seleccionada, "columns" :columns})
    else:
        # Manejar el caso donde no se seleccionó ninguna tabla
        return HttpResponse("No se seleccionó ninguna tabla.")
    
@login_required
@staff_member_required
def create_models(request):
    if request.method == 'POST':
        # Obtén el valor de modulesTelecommand como una cadena de texto
        modules_telecommand_str = request.POST.get('modulesTelecommand', '')
        modules_telecommand_list = modules_telecommand_str.split(',')
        
        asn_files = request.FILES.getlist('asn_files')
   
        # Validar tamaños de archivos
        MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
        for file in asn_files:
            if file.size > MAX_FILE_SIZE:
                return JsonResponse({'error': f'File size exceeds 1 MB limit: {file.name}'}, status=400)

        # Preparar los datos y archivos para enviar a la API Flask
        files = [('asn_files', (file.name, file.read(), file.content_type)) for file in asn_files]
        data = {
            'modulesTelecommand': ','.join(modules_telecommand_list),
            'keyspace': "tfm",
            'contact_points': "cassandra",
            'clusterPort': 9042
        }
        
        # Enviar solicitud POST con archivos y datos
        try:
            response = requests.post('http://as1scc:5000/create_models', data=data, files=files)
            response.raise_for_status()  # Lanza excepción para errores HTTP
            response_data = response.json()
            print(response_data)

            return JsonResponse(response_data)

        except requests.exceptions.RequestException as e:
            return render(request, 'create_models.html', {'error_message': f'Error al conectar con el servicio de ASN1SCC: {str(e)}'})
        

        # Comprobar si hay errores en la respuesta
        if response_data.get('error'):
            error_message = ""
            error_message = response_data['error']
            print(response_data)
            return render(request, 'create_models.html', {'error_message': "Error al crear las tablas: " + error_message})
        else:
            success_message = 'Tablas creadas correctamente'
            return render(request, 'create_models.html', {'success_message': success_message})

    return render(request, 'create_models.html')

    