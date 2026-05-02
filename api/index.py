import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SIGLO.settings')

def handler(request):
    from django.core.handlers.wsgi import WSGIHandler
    application = WSGIHandler()
    
    # Build the WSGI environment
    from io import BytesIO
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
    
    # Run Django
    from wsgiref.simple_server import make_environ_start_response
    
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
    
    # Parse response
    lines = response_text.split(b"\n")
    status_line = lines[0].decode()
    status_code = int(status_line.split()[1])
    
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