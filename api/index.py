from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# CONFIGURAÇÕES - Puxa as chaves do seu banco configurado na Vercel
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')
CHAVE_MESTRA = "1234"

def redis_call(command, key, value=None):
    if not KV_URL: return None
    parsed = urlparse(KV_URL)
    conn = http.client.HTTPSConnection(parsed.hostname)
    headers = {"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"}
    path = f"/{command}/{key}"
    
    method = "POST" if value is not None else "GET"
    body = json.dumps(value) if value is not None else None
    
    try:
        conn.request(method, path, body=body, headers=headers)
        res = conn.getresponse()
        raw_data = res.read().decode()
        conn.close()
        return json.loads(raw_data).get('result')
    except:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Validação da chave na URL (?key=1234)
        params = urlparse(self.path).query
        query_dict = dict(qc.split("=") for qc in params.split("&") if "=" in qc)
        
        if query_dict.get('key') != CHAVE_MESTRA:
            self.send_response(401)
            self.end_headers()
            return

        # Busca os dados que o seu PC enviou
        active_macs = redis_call("get", "active_devices")
        if not isinstance(active_macs, list): active_macs = []

        # Formata para o site exibir como "ALVO DETECTADO"
        data = [{"mac": m, "name": "ALVO DETECTADO"} for m in active_macs]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # LIBERA O SITE
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)
        
        if payload.get('key') == CHAVE_MESTRA:
            redis_call("set", "active_devices", payload.get('macs', []))
            self.send_response(200)
        else:
            self.send_response(403)
        self.end_headers()
