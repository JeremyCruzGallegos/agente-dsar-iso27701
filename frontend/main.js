'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const dsarForm = document.getElementById('dsarForm');
    const responseCard = document.getElementById('responseCard');
    const ticketIdSpan = document.getElementById('ticketId');
    const btnSubmit = document.getElementById('btnSubmit');
    const status = document.getElementById('formStatus');
    if (!dsarForm || !responseCard || !ticketIdSpan || !btnSubmit || !status) return;

    const webhookUrl = dsarForm.dataset.webhookUrl || 'http://localhost:5678/webhook/dsar-request';
    let sending = false;

    dsarForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (sending) return;
        for (const id of ['userId', 'email', 'details']) {
            const input = document.getElementById(id);
            input.value = input.value.trim();
        }
        if (!dsarForm.reportValidity()) return;

        const payload = {
            user_id: document.getElementById('userId').value,
            email: document.getElementById('email').value,
            request_type: document.getElementById('requestType').value,
            details: document.getElementById('details').value,
            timestamp: new Date().toISOString(),
        };
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);
        const buttonText = btnSubmit.textContent;
        sending = true;
        btnSubmit.disabled = true;
        btnSubmit.textContent = 'Enviando solicitud al agente...';
        responseCard.classList.add('hidden');
        ticketIdSpan.textContent = '';
        status.dataset.state = 'pending';
        status.textContent = 'Enviando solicitud…';

        try {
            const response = await fetch(webhookUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal,
            });
            if (!response.ok) {
                throw new Error(`n8n respondió con un error HTTP ${response.status}.`);
            }
            let result;
            try {
                result = await response.json();
            } catch (error) {
                if (error.name === 'AbortError') throw error;
                throw new Error('n8n no devolvió JSON válido. Verifica si se creó el ticket antes de reenviar.');
            }
            if (!result || result.status === 'error' ||
                typeof result.ticket_id !== 'string' || !result.ticket_id.trim()) {
                throw new Error('n8n no confirmó un ticket. Comprueba el flujo antes de reenviar.');
            }
            ticketIdSpan.textContent = result.ticket_id;
            dsarForm.classList.add('hidden');
            responseCard.classList.remove('hidden');
            status.dataset.state = 'success';
            status.textContent = 'Solicitud registrada correctamente.';
        } catch (error) {
            status.dataset.state = 'error';
            if (error.name === 'AbortError') {
                status.textContent = 'La respuesta tardó demasiado. Comprueba si se creó el ticket antes de reenviar.';
            } else if (error instanceof TypeError) {
                status.textContent = 'No se pudo conectar con n8n. Comprueba la conexión y CORS, y si se creó el ticket antes de reenviar.';
            } else {
                status.textContent = error.message;
            }
        } finally {
            clearTimeout(timeout);
            sending = false;
            btnSubmit.disabled = false;
            btnSubmit.textContent = buttonText;
        }
    });
});
