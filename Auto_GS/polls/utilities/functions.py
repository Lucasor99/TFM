from cassandra.cluster import Cluster
from Auto_GS.cassandra_conection import get_cassandra_session


#Insertar dato
def insert_data(data):
    session = get_cassandra_session()
    session.execute(
        """
        INSERT INTO example_dataview (example_dataview_sequence_number, dummy_telecommand__myinteger_payload, dummy_telecommand__myinteger_timestamp, dummy_telemetry__myinteger_payload, dummy_telemetry__myinteger_timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (data['example_dataview_sequence_number'], data['dummy_telecommand__myinteger_payload'],data['dummy_telecommand__myinteger_timestamp'], data['dummy_telemetry__myinteger_payload'],data['dummy_telemetry__myinteger_timestamp'])
    )

def select_by(table, key, value):
    try:
        session = get_cassandra_session()

        #Escrito así para evitar inyección
        query = f"SELECT * FROM {table} WHERE {key} = ? ALLOW FILTERING"
        prepared_query = session.prepare(query)
        result = session.execute(prepared_query, (value,))

        return result

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")


def update_data(table, key_column, key_value, column_to_update, new_value):
    try:
        session = get_cassandra_session()

        # Construir la consulta de actualización
        update_query = f"UPDATE {table} SET {column_to_update} = ? WHERE {key_column} = ?"

        # Preparar la consulta
        prepared_query = session.prepare(update_query)

        # Ejecutar la consulta con los parámetros necesarios
        session.execute(prepared_query, (new_value, key_value))

        print("Actualización exitosa.")

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")


def delete_data(table, column, value):
    try:
        # Establecer la conexión con el clúster de Cassandra
        session = get_cassandra_session()

        # Construir la consulta de actualización
        update_query = f"DELETE FROM {table} WHERE {column} = ?"
        # Preparar la consulta
        prepared_query = session.prepare(update_query)

        # Ejecutar la consulta con los parámetros necesarios
        session.execute(prepared_query, (value,))

        print("Actualización exitosa.")

    except Exception as e:
        print(f"Ha ocurrido un error: {str(e)}")



#Crear estructura de árbol

def create_tree_view(string_list, item):
    # Función para construir recursivamente el árbol
    def build_tree(node, path):
        if not path:
            return
        if path[0] not in [child['name'] for child in node.get('parameters', [])]:
            node.setdefault('parameters', []).append({'name': path[0]})
        child_node = next(child for child in node['parameters'] if child['name'] == path[0])
        build_tree(child_node, path[1:])

    # Crea la raíz del árbol
    tree = {'name': item, 'parameters': []}

    # Construye el árbol
    for string in string_list:
        build_tree(tree, string.split('_'))

    return tree


