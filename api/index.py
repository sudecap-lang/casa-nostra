from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Configurações do Redis (Vercel KV)
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
        raw = res.read().decode()
        conn.close()
        return json.loads(raw).get('result')
    except:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Libera o Opera
        self.send_header('Cache-Control', 'no-store') # Força dado novo
        self.end_headers()

        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps([]).encode())
            return

        # Puxa o dado do Redis
        raw_res = redis_call("get", "active_devices")
        
        # TRANSFORMAÇÃO CRÍTICA: Garante que o site receba uma lista []
        if isinstance(raw_res, list):
            data = raw_res
        elif raw_res:
            data = [raw_res] # Se for um texto único, vira lista
        else:
            data = []

        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)
        
        if payload.get('key') == CHAVE_MESTRA:
            # Salva o que vem do seu terminal
            macs = payload.get('macs', [])
            redis_call("set", "active_devices", macs)
            self.send_response(200)
        else:
            self.send_response(403)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
