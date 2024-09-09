from .common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Define los hosts permitidos en producción
ALLOWED_HOSTS = ['*']  # Cambia esto por tu dominio ejemplo: ['example.com']

# Base de datos para producción
DATABASES = {

    'default': {
        'NAME': 'user_data',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'admin',
        'PASSWORD': os.getenv('MYSQL_ROOT_PASSWORD'),
        'HOST': 'mysql',
        #'HOST': 'mysql.default.svc.cluster.local',
        'PORT': '3306',
    }
}

CASSANDRA= {
    'NAME': 'tfm',
    'USER': os.getenv('CASSANDRA_USER', 'cassandra'),  
    'PASSWORD': os.getenv('CASSANDRA_PASSWORD'),        
    'HOST': 'cassandra',
    'PORT': '9042',
    'contact_points': ['cassandra'],
}


# Pasword reset (Definir dominio y correo si se utiliza)

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_password' # os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'webmaster@example.com'


# Otros ajustes específicos de producción
#SECURE_SSL_REDIRECT = False  # Redirigir a HTTPS en producción. No necesario con nginx
#SECURE_CROSS_ORIGIN_OPENER_POLICY = None 
SECURE_CROSS_ORIGIN_OPENER_POLICY = "default-src 'self'; img-src 'self' https://*; connect-src 'self' http://asn1scc:5000;"

# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Añadir tu url de producción aquí
CSRF_TRUSTED_ORIGINS = ['https://*'] # Cambia esto por tu dirección de producción ejemplo: ['https://example.com']

