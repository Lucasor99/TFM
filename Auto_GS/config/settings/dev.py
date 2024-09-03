from .common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kda*0(j&_$*sqo)2h=xg1ga6g3ijb1#y=34#&$9f4pjaka_v6%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: don't use '*' in production!
ALLOWED_HOSTS = ['*']

# Base de datos para desarrollo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'cassandra': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'tfm',
        'USER': os.getenv('CASSANDRA_USER', 'cassandra'),  
        'PASSWORD': os.getenv('CASSANDRA_PASSWORD'),        
        'HOST': 'localhost',
        'PORT': '9042',
        'contact_points': ['localhost'],
    }
}

# Otros ajustes específicos de desarrollo
SECURE_SSL_REDIRECT = False  # No redirigir a HTTPS en desarrollo
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
