<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>COSA NOSTRA - PRIVADO</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        .header { border-bottom: 1px solid #333; padding-bottom: 10px; display: flex; justify-content: space-between; }
        .device-card { border: 1px solid #111; padding: 15px; margin: 10px 0; background: #050505; }
        .status-pulse { color: #0f0; font-size: 24px; }
        .error { color: #f00; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>COSA NOSTRA</h1>
            <p>NETWORK INTELLIGENCE</p>
        </div>
        <div id="counter" class="status-pulse">0</div>
    </div>

    <div id="content">Aguardando autorização...</div>

    <script>
        async function updateDashboard() {
            // Pega a chave direto do link (ex: ?key=1234)
            const urlParams = new URLSearchParams(window.location.search);
            const key = urlParams.get('key');

            if (!key) {
                document.getElementById('content').innerHTML = "<h2 class='error'>ERRO: ACESSO NEGADO. USE O LINK COM A CHAVE.</h2>";
                return;
            }

            try {
                const response = await fetch(`/api?key=${key}`);
                if (!response.ok) throw new Error("Chave incorreta");
                
                const data = await response.json();
                document.getElementById('counter').innerText = data.length;
                
                let html = "";
                data.forEach(dev => {
                    html += `<div class="device-card">
                                <strong>ALVO DETECTADO:</strong> ${dev.name}<br>
                                <small>MAC: ${dev.mac}</small>
                             </div>`;
                });
                document.getElementById('content').innerHTML = html || "Monitorando rede... Nenhum dispositivo ativo no momento.";
            } catch (err) {
                document.getElementById('content').innerHTML = "<h2 class='error'>ERRO DE CONEXÃO OU CHAVE INVÁLIDA</h2>";
            }
        }

        setInterval(updateDashboard, 5000); // Atualiza a cada 5 segundos
        updateDashboard();
    </script>
</body>
</html>
