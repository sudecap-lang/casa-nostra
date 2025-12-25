from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Ajustado para ler a variável REDIS_URL que aparece na sua imagem da Vercel
REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def redis_exec(cmd, key, val=None):
    if not REDIS_URL:
        return None
    try:
        # Remove o prefixo redis:// se existir para conseguir conectar via HTTPS
        url_limpa = REDIS_URL.replace("redis://", "https://")
        url = urlparse(url_limpa)
        
        # O token geralmente vem embutido na URL do Upstash/Vercel KV
        # Formato esperado: https://:TOKEN@HOST
        token = url.password
        host = url.hostname
        
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
    except Exception as e:
        print(f"Erro de Conexão Redis: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc) if query else {}
        
        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps([]).encode())
            return
            
        res = redis_exec("get", "active_devices")
        # Garante que sempre retornamos uma lista para o index.html não travar
        lista = [{"mac": "Alvo Detectado"}] if res else []
        self.wfile.write(json.dumps(lista).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                # Salva o valor 1 no banco de dados
                redis_exec("set", "active_devices", "1")
                self.send_response(200)
                self.end_headers()
        except:
            self.send_response(500)
            self.end_headers()
