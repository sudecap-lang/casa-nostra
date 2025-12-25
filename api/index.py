from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def redis_api(comando, path_extra=""):
    if not REDIS_URL: return None
    try:
        # Converte a URL do Redis para HTTPS (API REST do Upstash)
        url = urlparse(REDIS_URL.replace("redis://", "https://"))
        conn = http.client.HTTPSConnection(url.hostname, timeout=10)
        headers = {"Authorization": f"Bearer {url.password}"}
        
        # Formato: /comando/chave/valor
        conn.request("GET", f"/{comando}{path_extra}", headers=headers)
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
        
        # O site pede os dados aqui
        if params.get('key') == CHAVE_MESTRA:
            valor = redis_api("get", "/count")
            # Se no banco estiver "1", mandamos um item na lista para o site contar
            resposta = [{"id": 1}] if str(valor) == "1" else []
            self.wfile.write(json.dumps(resposta).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            # O Agente do PC avisa aqui que detectou algo
            if corpo.get('key') == CHAVE_MESTRA:
                redis_api("set", "/count/1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
