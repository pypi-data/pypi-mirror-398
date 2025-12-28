from setuptools import setup, find_packages

setup(
    name='starco-dj-utils',
    version='1.3.0',
    packages=['dj_utils'],
    include_package_data=True,
    license='MIT',
    description='A Django pluggable app for utilities and database management',
    author='Mojtaba',
    author_email='m.tahmasbi0111@yahoo.com',
    install_requires=[
        'Django>=4.0',
        'python-telegram-bot==22.5',
        'celery',
        'redis',
        'django-redis',
        'django-celery-beat',
        'colorama',
        'python-dotenv',
        'colorlog',
        'psycopg2-binary',
        'djangorestframework',
        'gunicorn',
        'uvicorn',
        'whitenoise',
        'setuptools',
        'wheel',
        'twine',
        'drf-spectacular',
        'django-modeltranslation',
        'django-cors-headers','django-filter','pillow','starco-utility','channels'

    ],
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ],
)
