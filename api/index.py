from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')
CHAVE_MESTRA = "1234"

def redis_exec(cmd, key, val=None):
    if not KV_URL: return None
    try:
        url = urlparse(KV_URL)
        conn = http.client.HTTPSConnection(url.hostname)
        headers = {"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"}
        path = f"/{cmd}/{key}"
        metodo = "POST" if val is not None else "GET"
        corpo = json.dumps(val) if val is not None else None
        conn.request(metodo, path, body=corpo, headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        conn.close()
        return data.get('result')
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
        if params.get('key') != CHAVE_MESTRA:
            self.wfile.write(json.dumps([]).encode())
            return
        res = redis_exec("get", "active_devices")
        lista = [{"mac": m} for m in res] if isinstance(res, list) else []
        self.wfile.write(json.dumps(lista).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            if corpo.get('key') == CHAVE_MESTRA:
                redis_exec("set", "active_devices", corpo.get('macs', []))
                self.send_response(200)
                self.end_headers()
        except:
            self.send_response(500)
            self.end_headers()
