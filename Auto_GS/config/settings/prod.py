from .common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Define los hosts permitidos en producción
ALLOWED_HOSTS = ['autogs.lucasor.com']  # Cambia esto por tu dominio

# Base de datos para producción
DATABASES = {
    'default': {
        'NAME': 'user_data',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'admin',
        'PASSWORD': os.getenv('MYSQL_ROOT_PASSWORD'),
        'HOST': 'mysql',
        'PORT': '3306',
    },
    'cassandra': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'tfm',
        'USER': os.getenv('CASSANDRA_USER', 'cassandra'),  
        'PASSWORD': os.getenv('CASSANDRA_PASSWORD'),        
        'HOST': 'cassandra',
        'PORT': '9042',
        'contact_points': ['cassandra'],
    }
}

# Otros ajustes específicos de producción
SECURE_SSL_REDIRECT = False  # Redirigir a HTTPS en producción
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False


