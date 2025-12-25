from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# CONFIGURAÇÕES - Puxa as chaves do banco redis-rose-yacht (STORAGE)
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')
CHAVE_MESTRA = "1234"

def redis_call(command, key, value=None):
    """Comunicação direta com o Banco de Dados Redis via REST API."""
    if not KV_URL: 
        return None
    
    parsed = urlparse(KV_URL)
    conn = http.client.HTTPSConnection(parsed.hostname)
    headers = {
        "Authorization": f"Bearer {KV_TOKEN}",
        "Content-Type": "application/json"
    }
    
    path = f"/{command}/{key}"
    method = "POST" if value is not None else "GET"
    body = json.dumps(value) if value is not None else None
    
    try:
        conn.request(method, path, body=body, headers=headers)
        res = conn.getresponse()
        raw_response = res.read().decode()
        conn.close()
        return json.loads(raw_response).get('result')
    except Exception:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Lê os dispositivos para exibir no site."""
        params = urlparse(self.path).query
        query_dict = {}
        if params:
            query_dict = dict(qc.split("=") for qc in params.split("&") if "=" in qc)
        
        # Verifica a chave de acesso (?key=1234)
        if query_dict.get('key') != CHAVE_MESTRA:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Acesso negado"}).encode())
            return

        # Busca a lista enviada pelo seu PC
        active_macs = redis_call("get", "active_devices")
        
        # Garante que seja uma lista para o site funcionar
        if not isinstance(active_macs, list):
            active_macs = []

        # Formata os dados para o dashboard
        data = [{"mac": m, "name": "DISPOSITIVO ATIVO"} for m in active_macs]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Libera para o navegador
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        """Recebe os dados do Agente Python do seu Desktop."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data)
        except:
            self.send_response(400)
            self.end_headers()
            return
        
        # Valida a chave enviada pelo seu PC
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

    def do_OPTIONS(self):
        """Trata requisições de segurança dos navegadores (CORS)."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
