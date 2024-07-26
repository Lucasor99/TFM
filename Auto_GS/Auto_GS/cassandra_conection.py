# cassandra_connection.py
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from django.conf import settings

def get_cassandra_session():
    db_settings = settings.DATABASES['cassandra']
    contact_points = db_settings['OPTIONS']['connection']['contact_points']
    keyspace = db_settings['KEYSPACE']
    user = db_settings['USER']
    password = db_settings['PASSWORD']

    # Configurar el proveedor de autenticación
    auth_provider = PlainTextAuthProvider(username=user, password=password)

    # Crear el cluster con el proveedor de autenticación
    cluster = Cluster(contact_points, auth_provider=auth_provider)
    session = cluster.connect()

    # Establecer el keyspace
    session.set_keyspace(keyspace)

    return session
