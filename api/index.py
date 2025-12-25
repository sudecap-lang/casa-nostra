from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# CONFIGURAÇÕES DO BANCO STORAGE (REDIS-ROSE-YACHT)
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')
CHAVE_MESTRA = "1234"

def redis_call(command, key, value=None):
    if not KV_URL or not KV_TOKEN: return None
    try:
        parsed = urlparse(KV_URL)
        conn = http.client.HTTPSConnection(parsed.hostname)
        headers = {"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"}
        path = f"/{command}/{key}"
        method = "POST" if value is not None else "GET"
        body = json.dumps(value) if value is not None else None
        conn.request(method, path, body=body, headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        conn.close()
        return data.get('result')
    except:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Captura parâmetros com segurança
        try:
            query = urlparse(self.path).query
            params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
        except:
            params = {}
        
        # Cabeçalhos obrigatórios para evitar erro no Edge/iOS/Opera
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

        # Verifica se a chave na URL está correta
        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps({"status": "bloqueado", "msg": "Use ?key=1234"}).encode())
            return

        # Puxa os dispositivos salvos
        res = redis_call("get", "active_devices")
        
        # Garante o formato de lista para o site contar
        if not isinstance(res, list):
            res = [res] if res else []
            
        final_data = [{"mac": m} for m in res if m]
        self.wfile.write(json.dumps(final_data).encode())

    def do_POST(self):
        # Recebe dados do agente local (CMD)
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data)
            
            if payload.get('key') == CHAVE_MESTRA:
                redis_call("set", "active_devices", payload.get('macs', []))
                self.send_response(200)
            else:
                self.send_response(403)
        except:
            self.send_response(500)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
