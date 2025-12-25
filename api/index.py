from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# CONFIGURAÇÕES DO BANCO STORAGE (REDIS)
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
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc) if query else {}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps({"error": "Chave invalida"}).encode())
            return

        # Busca os MACs enviados pelo seu terminal
        res = redis_call("get", "active_devices")
        
        # Garante que o site receba uma lista [] para o contador subir
        if isinstance(res, list):
            lista_formatada = [{"mac": m, "name": "ALVO"} for m in res]
        elif res:
            lista_formatada = [{"mac": str(res), "name": "ALVO"}]
        else:
            lista_formatada = []
            
        self.wfile.write(json.dumps(lista_formatada).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data)
            
            if payload.get('key') == CHAVE_MESTRA:
                redis_call("set", "active_devices", payload.get('macs', []))
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "sincronizado"}).encode())
            else:
                self.send_response(403)
                self.end_headers()
        except:
            self.send_response(400)
            self.end_headers()
