console.log('[Jarvis Content Script] Injetado na página:', window.location.href);

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    console.log('[Jarvis Content Script] Comando recebido:', request);

    const { action, target, value } = request;
    let result = { status: 'success' };

    try {
        if (action === 'scroll') {
            const amount = value ? parseInt(value) : 500;
            if (target === 'up') {
                window.scrollBy({ top: -amount, behavior: 'smooth' });
            } else {
                window.scrollBy({ top: amount, behavior: 'smooth' });
            }
        } 
        else if (action === 'click') {
            const el = document.querySelector(target);
            if (el) {
                el.click();
            } else {
                result = { status: 'error', message: 'Elemento não encontrado: ' + target };
            }
        }
        else if (action === 'type') {
            const el = document.querySelector(target);
            if (el) {
                el.value = value;
                // Disparar eventos para frameworks reativos notarem a mudança
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                result = { status: 'error', message: 'Elemento não encontrado: ' + target };
            }
        }
        else if (action === 'read') {
            // Extrai o texto visível da página
            result = { status: 'success', text: document.body.innerText.substring(0, 5000) };
        }
        else {
            result = { status: 'error', message: 'Ação desconhecida: ' + action };
        }
    } catch (e) {
        result = { status: 'error', message: e.toString() };
    }

    sendResponse(result);
    return true; // Keep the message channel open for async response
});
