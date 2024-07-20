### Alternativa para que el usuario ponga en el fichero los parámetros de configuración


from cassandra.cluster import Cluster

# Connect to the container cassandra
cluster = Cluster(['cassandra'], port=9042)
keyspace = 'tfm'
createKeyspace="CREATE KEYSPACE IF NOT EXISTS %s WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : '3' }"  % keyspace
session=cluster.connect()
session.execute(createKeyspace)
session.set_keyspace(keyspace) 

