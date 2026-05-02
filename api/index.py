import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SIGLO.settings')

from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()

def handler(request):
    from io import BytesIO
    from wsgiref.headers import Headers
    
    body = request.get('body', '') or ''
    environ = {
        'REQUEST_METHOD': request.get('httpMethod', 'GET'),
        'PATH_INFO': request.get('path', '/'),
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'HTTP_HOST': request.get('headers', {}).get('host', 'localhost'),
        'wsgi.input': BytesIO(body.encode() if body else b''),
        'wsgi.errors': sys.stderr,
        'wsgi.url_scheme': 'https',
    }
    
    output = BytesIO()
    def start_response(status, headers):
        output.write(f"HTTP/1.1 {status}\n".encode())
        for k, v in headers:
            output.write(f"{k}: {v}\n".encode())
        output.write(b"\n")
        return output.write
    
    result = application(environ, start_response)
    response_body = b"".join(result)
    response_text = output.getvalue() + response_body
    
    lines = response_text.split(b"\n")
    status_code = int(lines[0].decode().split()[1])
    
    headers = {}
    body_start = 0
    for i, line in enumerate(lines[1:], 1):
        if line == b"":
            body_start = i + 1
            break
        if b":" in line:
            k, v = line.split(b":", 1)
            headers[k.decode().strip()] = v.decode().strip()
    
    body = b"\n".join(lines[body_start:]).decode('utf-8', errors='replace')
    
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": body
    }