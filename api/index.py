from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Pega a URL do banco Redis que você configurou na Vercel
REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def acessar_redis(metodo, path, corpo=None):
    if not REDIS_URL: return None
    try:
        url = urlparse(REDIS_URL.replace("redis://", "https://"))
        conn = http.client.HTTPSConnection(url.hostname, timeout=10)
        headers = {
            "Authorization": f"Bearer {url.password}",
            "Content-Type": "application/json"
        }
        conn.request(metodo, path, body=json.dumps(corpo) if corpo else None, headers=headers)
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
            # Lê o valor gravado pelo agente do desktop
            valor = acessar_redis("GET", "/get/count")
            # Se o valor for "1", envia uma lista com 1 item para o site mostrar "1"
            resultado = [{"status": "on"}] if str(valor) == "1" else []
            self.wfile.write(json.dumps(resultado).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                # O Agente do desktop usa este POST para avisar que detectou algo
                acessar_redis("GET", "/set/count/1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
