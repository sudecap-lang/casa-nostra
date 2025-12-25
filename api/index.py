from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# CONFIGURAÇÕES
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')
CHAVE_MESTRA = "1234"

def redis_call(command, key, value=None):
    """Comunicação com o Redis (Vercel KV)"""
    if not KV_URL or not KV_TOKEN:
        return None
    
    try:
        parsed = urlparse(KV_URL)
        conn = http.client.HTTPSConnection(parsed.hostname)
        headers = {
            "Authorization": f"Bearer {KV_TOKEN}",
            "Content-Type": "application/json"
        }
        
        path = f"/{command}/{key}"
        method = "POST" if value is not None else "GET"
        body = json.dumps(value) if value is not None else None
        
        conn.request(method, path, body=body, headers=headers)
        res = conn.getresponse()
        data = res.read().decode()
        conn.close()
        return json.loads(data).get('result')
    except Exception as e:
        print(f"Erro no Redis: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Evita erro de parsing se a URL for curta
        query = urlparse(self.path).query
        params = {}
        if query:
            try:
                params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
            except:
                params = {}

        # Resposta padrão para evitar página branca
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Validação da chave
        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps({"status": "error", "message": "Chave invalida"}).encode())
            return

        # Busca dados no banco
        active_macs = redis_call("get", "active_devices")
        
        # Garante que sempre retorne uma lista para o site index.html
        if not isinstance(active_macs, list):
            active_macs = []

        # Formato esperado pelo seu site
        final_data = [{"mac": m, "name": "ALVO LOCALIZADO"} for m in active_macs]
        self.wfile.write(json.dumps(final_data).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data)
            
            if payload.get('key') == CHAVE_MESTRA:
                macs = payload.get('macs', [])
                redis_call("set", "active_devices", macs)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "sincronizado"}).encode())
            else:
                self.send_response(403)
                self.end_headers()
        except Exception:
            self.send_response(400)
            self.end_headers()
