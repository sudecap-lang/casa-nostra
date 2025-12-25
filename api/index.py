from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Usa a variável exata que aparece na sua foto da Vercel
REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def redis_exec(cmd, key, val=None):
    if not REDIS_URL:
        return None
    try:
        # Converte a URL do Redis para HTTPS para o Upstash/Vercel
        url_limpa = REDIS_URL.replace("redis://", "https://")
        url = urlparse(url_limpa)
        host = url.hostname
        token = url.password
        
        conn = http.client.HTTPSConnection(host)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        path = f"/{cmd}/{key}"
        metodo = "POST" if val is not None else "GET"
        corpo = json.dumps(val) if val is not None else None
        
        conn.request(metodo, path, body=corpo, headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        conn.close()
        return data.get('result')
    except:
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
            # Se o banco tiver algo, mandamos uma lista com 1 item para o monitor mostrar "1"
            self.wfile.write(json.dumps([{"status": "ativo"}] if res == "1" else []).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                redis_exec("set", "count", "1")
                self.send_response(200)
                self.end_headers()
        except:
            self.send_response(500)
            self.end_headers()
