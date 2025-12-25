from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Puxa as chaves do banco redis-rose-yacht
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
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
        
        # RESPOSTA DE CABEÇALHO (CORS)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()

        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps({"error": "Chave incorreta"}).encode())
            return

        # Busca os dados enviados pelo seu terminal
        active_macs = redis_call("get", "active_devices")
        
        # Converte para o formato que o seu site Cosa Nostra espera
        if isinstance(active_macs, list):
            lista_final = [{"mac": m, "name": "ALVO DETECTADO"} for m in active_macs if m]
        elif active_macs:
            lista_final = [{"mac": active_macs, "name": "ALVO DETECTADO"}]
        else:
            lista_final = []

        self.wfile.write(json.dumps(lista_final).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)
        
        if payload.get('key') == CHAVE_MESTRA:
            redis_call("set", "active_devices", payload.get('macs', []))
            self.send_response(200)
        else:
            self.send_response(403)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
