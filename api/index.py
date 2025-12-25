from http.server import BaseHTTPRequestHandler
import json
import os
import http.client
from urllib.parse import urlparse

# Usa a variável que aparece no seu print da Vercel
REDIS_URL = os.environ.get('REDIS_URL')
CHAVE_MESTRA = "1234"

def gerenciar_banco(metodo, acao):
    if not REDIS_URL: return None
    try:
        # Converte o link do Redis para o formato de API HTTPS
        url = urlparse(REDIS_URL.replace("redis://", "https://"))
        conn = http.client.HTTPSConnection(url.hostname, timeout=10)
        headers = {"Authorization": f"Bearer {url.password}"}
        
        # Executa o comando no banco (ex: /set/alvo/1)
        conn.request(metodo, acao, headers=headers)
        res = conn.getresponse()
        dados = json.loads(res.read().decode())
        conn.close()
        return dados.get('result')
    except:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # O site pergunta aqui: "Tem alguém?"
        valor = gerenciar_banco("GET", "/get/alvo")
        
        # Se o banco tiver "1", o site mostra o número 1
        resultado = [{"detectado": True}] if str(valor) == "1" else []
        self.wfile.write(json.dumps(resultado).encode())

    def do_POST(self):
        try:
            tamanho = int(self.headers['Content-Length'])
            corpo = json.loads(self.rfile.read(tamanho))
            
            # O Agente do PC avisa aqui que o sistema está online
            if corpo.get('key') == CHAVE_MESTRA:
                gerenciar_banco("GET", "/set/alvo/1")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
        except:
            self.send_response(500)
            self.end_headers()
