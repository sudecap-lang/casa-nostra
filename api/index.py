from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# Chaves do banco (mantendo o prefixo STORAGE que você configurou)
KV_URL = os.environ.get('STORAGE_REST_API_URL')
KV_TOKEN = os.environ.get('STORAGE_REST_API_TOKEN')

# --- DEFINA SUA SENHA AQUI ---
CHAVE_MESTRA = "1234" 

def redis_set(key, value):
    if not KV_URL: return
    requests.post(f"{KV_URL}/set/{key}", headers={"Authorization": f"Bearer {KV_TOKEN}"}, data=json.dumps(value))

def redis_get(key):
    if not KV_URL: return None
    r = requests.get(f"{KV_URL}/get/{key}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
    return r.json().get('result')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Proteção: O site só responde se você colocar ?key=1234 no final do link
        params = self.path.split('?')
        provided_key = ""
        if len(params) > 1:
            for p in params[1].split('&'):
                if p.startswith('key='): provided_key = p.split('=')[1]

        if provided_key != CHAVE_MESTRA:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"ACESSO NEGADO: Use a chave correta.")
            return

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
        
        # O Agente Windows também precisa enviar a chave
        if payload.get('key') != CHAVE_MESTRA:
            self.send_response(403)
            self.end_headers()
            return

        if 'macs' in payload:
            redis_set('active_devices', payload['macs'])
        
        if 'rename' in payload:
            nicks = redis_get('nicknames') or {}
            nicks[payload['mac']] = payload['rename']
            redis_set('nicknames', nicks)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
