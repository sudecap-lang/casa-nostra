from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Puxa as chaves do banco redis-rose-yacht (Configurado nas suas fotos)
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')
CHAVE_MESTRA = "1234"

def redis_call(command, key, value=None):
    if not KV_URL: return None
    parsed = urlparse(KV_URL)
    conn = http.client.HTTPSConnection(parsed.hostname)
    headers = {"Authorization": f"Bearer {KV_TOKEN}"}
    path = f"/{command}/{key}"
    body = json.dumps(value) if value is not None else None
    method = "POST" if value is not None else "GET"
    conn.request(method, path, body=body, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    return json.loads(data).get('result')

class handler(BaseHTTPRequestHandler):
   def do_GET(self):
        params = urlparse(self.path).query
        query_dict = dict(qc.split("=") for qc in params.split("&") if "=" in qc)
        
        if query_dict.get('key') != CHAVE_MESTRA:
            self.send_response(401)
            self.end_headers()
            return

        # Busca a lista de MACs enviada pelo seu PC
        active_macs = redis_call("get", "active_devices") or []
        
        # Garante que o formato seja uma lista de objetos que o site entenda
        data = [{"mac": m, "name": "ALVO DETECTADO"} for m in active_macs]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Libera o acesso para o site
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)
        
        if payload.get('key') != CHAVE_MESTRA:
            self.send_response(403)
            self.end_headers()
            return

        if 'macs' in payload:
            redis_call("set", "active_devices", payload['macs'])
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
