document.addEventListener('DOMContentLoaded', () => {
    const $ = id => document.getElementById(id);
    let key = '';
    async function api(path, options = {}) {
        const response = await fetch('/api' + path, { ...options, headers: { 'Content-Type': 'application/json', 'X-API-Key': key, ...(options.headers || {}) } });
        const body = await response.json();
        if (!response.ok) throw new Error(body.error?.message || 'No se pudo completar la operación.');
        return body.data;
    }
    $('loginForm').addEventListener('submit', async event => {
        event.preventDefault(); key = $('apiKey').value;
        try {
            const state = await api('/ai/status');
            if (!state.ready) throw new Error(state.message);
            $('workspace').classList.remove('hidden'); $('loginForm').classList.add('hidden'); $('logoutButton').classList.remove('hidden');
            $('status').textContent = `Base lista: ${state.documents} documentos y ${state.chunks} fragmentos.`;
        } catch (error) { key = ''; $('status').textContent = error.message; }
    });
    $('logoutButton').onclick = () => { key = ''; $('apiKey').value = ''; $('workspace').classList.add('hidden'); $('answerCard').classList.add('hidden'); $('loginForm').classList.remove('hidden'); $('logoutButton').classList.add('hidden'); $('status').textContent = 'Sesión cerrada.'; };
    $('caseForm').addEventListener('submit', async event => {
        event.preventDefault(); const button = $('analyzeButton'); button.disabled = true; $('status').textContent = 'Buscando fundamentos…';
        try {
            const data = await api('/case-analysis', { method: 'POST', body: JSON.stringify({ case: $('caseText').value }) });
            $('answer').textContent = data.answer; $('notice').textContent = data.notice; $('evidence').replaceChildren();
            for (const item of data.evidence) {
                const article = document.createElement('article'); article.className = 'search-result';
                const title = document.createElement('h3'); title.textContent = `[${item.id}] ${item.source}${item.section ? ' — ' + item.section : ''}`;
                const score = document.createElement('p'); score.className = 'help'; score.textContent = `Similitud temática: ${Number(item.score).toFixed(3)}`;
                const excerpt = document.createElement('p'); excerpt.className = 'excerpt'; excerpt.textContent = item.excerpt;
                article.append(title, score, excerpt); $('evidence').append(article);
            }
            $('answerCard').classList.remove('hidden'); $('status').textContent = data.evidence.length ? 'Análisis terminado.' : 'No se encontró evidencia suficiente.';
        } catch (error) { $('status').textContent = error.message; } finally { button.disabled = false; }
    });
});
