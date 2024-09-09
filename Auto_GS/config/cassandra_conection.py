from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from django.conf import settings

def get_cassandra_session():
    db_settings = settings.CASSANDRA
    contact_points = db_settings['contact_points']
    keyspace = db_settings['NAME']
    user = db_settings['USER']
    password = db_settings['PASSWORD']

    # Configurar el proveedor de autenticación
    auth_provider = PlainTextAuthProvider(username=user, password=password)

    try:
        # Crear el cluster con el proveedor de autenticación
        cluster = Cluster(contact_points, auth_provider=auth_provider)
        session = cluster.connect()

        # Establecer el keyspace
        session.set_keyspace(keyspace)

        return session

    except Exception as e:
        print(f"No se ha podido conectar con la base de datos Cassandra")
        return None
