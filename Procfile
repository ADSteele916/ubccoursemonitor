release: python manage.py migrate --no-input
web: gunicorn ubccoursemonitor.wsgi
worker: celery worker -A ubccoursemonitor --beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler