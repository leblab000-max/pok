"""Loopback-only HTTP boundary with token, origin and host checks."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import hmac
import json
import secrets
from .session import Session, Conflict

STATIC = Path(__file__).with_name('static')

class SandboxServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, directory, port=8765, *, session=None):
        self.session = session or Session(directory)
        self.token = secrets.token_urlsafe(32)
        try: super().__init__(('127.0.0.1',port), Handler)
        except BaseException:
            self.session.close();raise
        self.url = f'http://127.0.0.1:{self.server_port}'
    def server_close(self):
        super().server_close();self.session.close()

class Handler(BaseHTTPRequestHandler):
    server: SandboxServer
    def log_message(self, *args): pass  # Never write the session token in access logs.
    def reply(self,status,data,content_type='application/json; charset=utf-8'):
        payload=json.dumps(data,ensure_ascii=False).encode() if content_type.startswith('application/json') else data
        self.send_response(status)
        for k,v in {'Content-Type':content_type,'Content-Length':str(len(payload)),
                    'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
                    'Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
                    'Content-Security-Policy':"default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}.items():
            self.send_header(k,v)
        self.end_headers()
        try:self.wfile.write(payload)
        except (BrokenPipeError,ConnectionResetError): pass
    def allowed(self, api=False):
        port=self.server.server_port
        hosts=(f'127.0.0.1:{port}',f'localhost:{port}')
        if self.headers.get('Host') not in hosts: return False
        origin=self.headers.get('Origin')
        if origin and origin not in tuple(f'http://{h}' for h in hosts): return False
        if self.headers.get('Sec-Fetch-Site')=='cross-site': return False
        return not api or hmac.compare_digest(self.headers.get('X-Poker-Token',''),self.server.token)
    def do_GET(self):
        path=urlsplit(self.path).path
        if not self.allowed(path.startswith('/api/')): return self.reply(403,dict(error='Local session authentication required'))
        if path=='/api/state': return self.reply(200,self.server.session.snapshot())
        if path=='/health': return self.reply(200,dict(ok=True,application='poker-sandbox'))
        mapping={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/app.css':('app.css','text/css; charset=utf-8')}
        if path=='/favicon.ico': return self.reply(204,b'','image/x-icon')
        if path not in mapping: return self.reply(404,dict(error='Not found'))
        name,kind=mapping[path];data=(STATIC/name).read_bytes()
        if name=='index.html': data=data.replace(b'__SESSION_TOKEN__',self.server.token.encode())
        self.reply(200,data,kind)
    def do_POST(self):
        if not self.allowed(True): return self.reply(403,dict(error='Local session authentication required'))
        try:
            if self.headers.get('Content-Type','').split(';')[0]!='application/json': raise ValueError('JSON required')
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=65536: raise ValueError('Invalid body size')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict): raise ValueError('JSON object required')
            path=urlsplit(self.path).path
            if path not in tuple('/api/'+c for c in ('start','pause','stop','reset','step','action')):
                return self.reply(404,dict(error='Not found'))
            self.reply(200,self.server.session.command(path.rsplit('/',1)[1],body))
        except Conflict as exc: self.reply(409,dict(error=str(exc)))
        except (ValueError,TypeError) as exc:
            self.server.session.error(f'Rejected request: {exc}')
            self.reply(422,dict(error=str(exc)))
        except Exception:
            self.server.session.logger.exception('HTTP request failed')
            self.reply(500,dict(error='Request failed; see errors.log'))
