from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def redis_exec(cmd, key, val=None):
    if not REDIS_URL: return None
    try:
        # Transforma redis:// em https:// para a API REST do Upstash
        url_limpa = REDIS_URL.replace("redis://", "https://")
        url = urlparse(url_limpa)
        conn = http.client.HTTPSConnection(url.hostname, timeout=10)
        
        headers = {
            "Authorization": f"Bearer {url.password}",
            "Content-Type": "application/json"
        }
        
        path = f"/{cmd}/{key}/{val if val else ''}"
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        conn.close()
        return data.get('result')
    except Exception as e:
        print(f"Erro Redis: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc) if query else {}
        
        if params.get('key') == CHAVE_MESTRA:
            res = redis_exec("get", "count")
            # Se o valor no banco for "1", o site mostra 1
            status = [{"mac": "detectado"}] if str(res) == "1" else []
            self.wfile.write(json.dumps(status).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                # Grava o número 1 no banco
                redis_exec("set", "count", "1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
