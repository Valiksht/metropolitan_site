from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())

DEBUG = os.getenv("DEBUG_STATUS", "True") == "True"
# DEBUG = True

ALLOWED_HOSTS = [
    os.getenv('ALLOWED_HOSTS_ID'),
    os.getenv('ALLOWED_HOSTS_URL'),
    os.getenv('ALLOWED_HOSTS_URL_WWW'),
    'localhost',
    '127.0.0.1'
]

INSTALLED_APPS = [
    'adminsortable2',
    'django_cleanup',
    'temple.apps.TempleConfig',
    'core.apps.CoreConfig',
    'backups.apps.BackupsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ckeditor_5',
    'dbbackup'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cstovo.urls'

TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
# TEMPLATES_DIR = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'temple.context_processors.dropdown_list',
                'temple.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'cstovo.wsgi.application'

if DEBUG:
    # Локальная база для разработки (простая sqlite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Боевая база (PostgreSQL), параметры берём из окружения
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'django'),
            'USER': os.getenv('POSTGRES_USER', 'django'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'db'),
            'PORT': os.getenv('DB_PORT', 5432),
        }
    }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('POSTGRES_DB', 'django'),
#         'USER': os.getenv('POSTGRES_USER', 'django'),
#         'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
#         'HOST': os.getenv('DB_HOST', 'db'),
#         'PORT': os.getenv('DB_PORT', 5432)
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         # 'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
     'location': os.path.join(BASE_DIR, 'tmp_backups'),
     }
DBBACKUP_MEDIA_PATH = 'media'  # для mediabackup
DBBACKUP_COMPRESS = True

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['bold', 'italic', 'underline', '|', 'bulletedList', 'numberedList', '|', 'link', '|', 'undo', 'redo'],
        'language': 'ru',
        'height': 300,
    },
    'full': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'blockQuote', 'insertTable', '|', 'link', 'imageUpload', '|', 'undo', 'redo'],
        'image': {
            'toolbar': ['imageTextAlternative'],
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells'],
        },
    },
}

CKEDITOR_5_ALLOWED_CONTENT = True
