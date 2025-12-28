import os
from dotenv import load_dotenv

load_dotenv()
INSTALLED_APPS += [
    'rest_framework',
    'django_celery_beat',
    'rest_framework.authtoken',
    'drf_spectacular',
]
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")
INSTALLED_APPS.insert(0, "modeltranslation")
#############################################
DEBUG = bool(int(str(os.getenv('DEBUG', 0))))
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(' ')
trusted_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if trusted_origins:
    CSRF_TRUSTED_ORIGINS = trusted_origins.split(' ')
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "")
if ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = ALLOWED_ORIGINS.split(' ')
#############################################
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'
#############################################
postgresql = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv("POSTGRES_DB"),
    'USER': os.getenv("POSTGRES_USER"),
    'PASSWORD': os.getenv("POSTGRES_PASSWORD"),
    'HOST': os.getenv("POSTGRES_HOST"),
    'PORT': os.getenv("POSTGRES_PORT"),
}
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS':'dj_utils.render.pagination.FullLinkPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES':[
        'dj_utils.render.api_response_handler.StandardResponseRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv("CACHE_URL"),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
#############################################
import sys
import colorlog

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'colored',
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
#############################################
# Celery settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
#############################################
if os.getenv("DJANGO_ENV") != "build":
    DATABASES['default'] = postgresql
#############################################

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Project API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}
#############################################

if str(os.getenv("MULTI_LANGUAGES"))=='1':
    import logging
    logging.debug('Multi-Languages is enabled')
    index_SessionMiddleware = MIDDLEWARE.index("django.contrib.sessions.middleware.SessionMiddleware")
    MIDDLEWARE.insert(index_SessionMiddleware+1, "django.middleware.locale.LocaleMiddleware")
    LANGUAGE_CODE = 'en'     # زبان پیش‌فرض
    USE_I18N = True

    LANGUAGES = [
        ('en', 'English'),
        ('fa', 'Persian'),
    ]

    LOCALE_PATHS = [
        BASE_DIR / 'locale'
    ]

