from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def redis_call(path):
    if not REDIS_URL: return None
    try:
        url = urlparse(REDIS_URL.replace("redis://", "https://"))
        conn = http.client.HTTPSConnection(url.hostname, timeout=10)
        headers = {"Authorization": f"Bearer {url.password}"}
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        conn.close()
        return data.get('result')
    except: return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc) if query else {}
        
        if params.get('key') == CHAVE_MESTRA:
            # Busca o valor da chave 'count' no Redis
            res = redis_call("/get/count")
            # Se for "1", mandamos a lista que ativa o monitor
            saida = [{"status": "online"}] if str(res) == "1" else []
            self.wfile.write(json.dumps(saida).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                # Define o contador como 1 no banco
                redis_call("/set/count/1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
