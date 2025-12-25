from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Pega a URL que você configurou na imagem da Vercel
REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def redis_exec(cmd, key, val=None):
    if not REDIS_URL: return None
    try:
        # Força HTTPS e limpa a URL
        url_limpa = REDIS_URL.replace("redis://", "https://")
        url = urlparse(url_limpa)
        conn = http.client.HTTPSConnection(url.hostname, timeout=5)
        
        headers = {
            "Authorization": f"Bearer {url.password}",
            "Content-Type": "application/json"
        }
        
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
            # Se houver qualquer valor no banco, mandamos "ativo" para o monitor
            self.wfile.write(json.dumps([{"mac": "ALVO_LOCAL"}] if res else []).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                # Salva o valor "1" de forma simplificada
                redis_exec("set", "count", "1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
