from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# Ajustado para o prefixo que aparece nas suas fotos (STORAGE)
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')

def redis_set(key, value):
    if not KV_URL: return
    url = f"{KV_URL}/set/{key}"
    requests.post(url, headers={"Authorization": f"Bearer {KV_TOKEN}"}, data=json.dumps(value))

def redis_get(key):
    if not KV_URL: return None
    url = f"{KV_URL}/get/{key}"
    r = requests.get(url, headers={"Authorization": f"Bearer {KV_TOKEN}"})
    return r.json().get('result')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        active_macs = redis_get('active_devices') or []
        nicknames = redis_get('nicknames') or {}
        
        data = [{"mac": m, "name": nicknames.get(m, "ALVO DETECTADO")} for m in active_macs]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)
        
        if 'macs' in payload:
            redis_set('active_devices', payload['macs'])
        
        if 'rename' in payload:
            nicks = redis_get('nicknames') or {}
            nicks[payload['mac']] = payload['rename']
            redis_set('nicknames', nicks)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
