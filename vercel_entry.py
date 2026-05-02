#!/usr/bin/env python
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SIGLO.settings')

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
    
    from waitress import serve
    from SIGLO.wsgi import application
    serve(application, host='0.0.0.0', port=8000)