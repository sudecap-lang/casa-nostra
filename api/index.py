from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Pega o link do banco que aparece no seu print da Vercel
REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def gerenciar_redis(cmd, path_final):
    if not REDIS_URL: return None
    try:
        # Converte redis:// para https:// para usar a API do Upstash
        url = urlparse(REDIS_URL.replace("redis://", "https://"))
        conn = http.client.HTTPSConnection(url.hostname, timeout=10)
        headers = {"Authorization": f"Bearer {url.password}"}
        
        # Executa o comando (ex: /get/count ou /set/count/1)
        conn.request("GET", f"/{cmd}{path_final}", headers=headers)
        res = conn.getresponse()
        corpo = json.loads(res.read().decode())
        conn.close()
        return corpo.get('result')
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
            # Lê o valor do banco
            valor = gerenciar_redis("get", "/count")
            # Se o banco tiver "1", enviamos 1 item para o site contar
            resultado = [{"status": "on"}] if str(valor) == "1" else []
            self.wfile.write(json.dumps(resultado).encode())
        else:
            self.wfile.write(json.dumps([]).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                # O Agente do PC avisa que o alvo está online
                gerenciar_redis("set", "/count/1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
