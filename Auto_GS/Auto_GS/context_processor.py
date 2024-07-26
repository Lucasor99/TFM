from cassandra.cluster import Cluster
from .cassandra_conection import get_cassandra_session

def user_info(request):
    if request.user.is_authenticated:
        return {
            'username': request.user.username,
            'email': request.user.email,
        }
    return {}


def nav_items_processor(request):
    session = get_cassandra_session()

    nav_items = []
    aux = session.execute("describe tables")

    for row in aux:
        nav_items.append(row.name)

    return {'nav_items': nav_items}