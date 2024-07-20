from cassandra.cluster import Cluster


def user_info(request):
    if request.user.is_authenticated:
        return {
            'username': request.user.username,
            'email': request.user.email,
        }
    return {}


def nav_items_processor(request):
    contact_points = ['cassandra']
    cluster = Cluster(contact_points)
    session = cluster.connect()
    keyspace_query = "CREATE KEYSPACE IF NOT EXISTS tfm WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}"
    session.execute(keyspace_query)

    session.set_keyspace('tfm')

    nav_items = []
    aux = session.execute("describe tables")

    for row in aux:
        nav_items.append(row.name)

    return {'nav_items': nav_items}