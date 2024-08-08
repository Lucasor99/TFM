### Alternativa para que el usuario ponga en el fichero los parámetros de configuración
import os

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Connect to the container cassandra
auth_provider = PlainTextAuthProvider(username=os.getenv('CASSANDRA_USER', 'cassandra'), password=os.getenv('CASSANDRA_PASSWORD'))
cluster = Cluster(['cassandra'], auth_provider=auth_provider)
keyspace = 'tfm'
createKeyspace="CREATE KEYSPACE IF NOT EXISTS %s WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : '3' }"  % keyspace
session=cluster.connect()
session.execute(createKeyspace)
session.set_keyspace(keyspace) 

