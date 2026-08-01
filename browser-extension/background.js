let socket = null;
let reconnectInterval = 5000;

function connectWebSocket() {
    socket = new WebSocket('ws://localhost:8080/ws/browser');

    socket.onopen = () => {
        console.log('[Jarvis Bridge] Conectado ao servidor.');
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('[Jarvis Bridge] Comando recebido:', data);
            
            // Send command to the active tab
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, data, function(response) {
                        console.log('[Jarvis Bridge] Resposta da aba:', response);
                        // Se precisarmos enviar a resposta de volta ao Python, faríamos aqui:
                        // socket.send(JSON.stringify(response));
                    });
                }
            });
        } catch (e) {
            console.error('[Jarvis Bridge] Erro ao parsear mensagem:', e);
        }
    };

    socket.onclose = () => {
        console.log('[Jarvis Bridge] Desconectado. Tentando reconectar...');
        setTimeout(connectWebSocket, reconnectInterval);
    };

    socket.onerror = (error) => {
        console.error('[Jarvis Bridge] Erro no WebSocket:', error);
        socket.close();
    };
}

// Inicializa a conexão
connectWebSocket();
