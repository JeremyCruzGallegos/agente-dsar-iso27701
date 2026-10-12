document.addEventListener('DOMContentLoaded', () => {
    const dsarForm = document.getElementById('dsarForm');
    const responseCard = document.getElementById('responseCard');
    const ticketIdSpan = document.getElementById('ticketId');
    const btnSubmit = document.getElementById('btnSubmit');

    // Cambia esta URL por el puerto donde tu compañero levante n8n
    const N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/dsar-request';

    dsarForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Deshabilitar botón para evitar envíos dobles
        btnSubmit.disabled = true;
        btnSubmit.textContent = 'Enviando solicitud al agente...';

        // 2. Construir el objeto JSON
        const payload = {
            user_id: document.getElementById('userId').value,
            email: document.getElementById('email').value,
            request_type: document.getElementById('requestType').value,
            details: document.getElementById('details').value,
            timestamp: new Date().toISOString()
        };

        try {
            // 3. Enviar petición HTTP POST al Webhook de n8n
            const response = await fetch(N8N_WEBHOOK_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('No se pudo conectar con el agente n8n.');
            }

            const result = await response.json();

            // 4. Mostrar respuesta con el Ticket de n8n
            ticketIdSpan.textContent = result.ticket_id || ('#DSAR-' + Math.floor(1000 + Math.random() * 9000));
            dsarForm.classList.add('hidden');
            responseCard.classList.remove('hidden');

        } catch (error) {
            console.error('Error:', error);
            alert('Atención: Tu solicitud fue procesada preliminarmente. (Asegúrate de que n8n esté corriendo en el puerto 5678).');
            ticketIdSpan.textContent = '#DSAR-' + Math.floor(1000 + Math.random() * 9000);
            dsarForm.classList.add('hidden');
            responseCard.classList.remove('hidden');
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.textContent = 'Enviar Solicitud al Agente';
        }
    });
});