document.addEventListener('DOMContentLoaded', () => {
    const $ = id => document.getElementById(id);
    let key = '', history = [], conversationVersion = 0;

    async function api(path, options = {}) {
        const response = await fetch('/api' + path, { ...options, headers: {
            'Content-Type': 'application/json', 'X-API-Key': key, ...(options.headers || {})
        }});
        const body = await response.json();
        if (!response.ok) throw new Error(body.error?.message || 'No se pudo completar la operación.');
        return body.data;
    }

    function message(role, content, data) {
        const article = document.createElement('article'); article.className = `chat-message ${role}`;
        const heading = document.createElement('h3'); heading.textContent = role === 'user' ? 'Tú' : 'Agente';
        const text = document.createElement('p'); text.className = 'chat-text'; text.textContent = content;
        article.append(heading, text);
        if (data) {
            const meta = document.createElement('p'); meta.className = 'help';
            meta.textContent = data.mode === 'generative_rag'
                ? `Conclusión generada por ${data.model} · confianza ${data.confidence}`
                : data.mode === 'document_selection' ? `Pasajes seleccionados por ${data.model} · texto del ejercicio académico`
                : data.coverage === 'insufficient_evidence' ? 'Sin evidencia para esta consulta.' : 'Consulta documental · sin conclusión generada.';
            article.append(meta);
            if (data.limitations?.length) {
                const details = document.createElement('details'), summary = document.createElement('summary');
                summary.textContent = 'Límites del análisis';
                const list = document.createElement('ul');
                data.limitations.forEach(value => { const item = document.createElement('li'); item.textContent = value; list.append(item); });
                details.append(summary, list); article.append(details);
            }
            if (data.case_guides?.length) {
                const guideDetails = document.createElement('details');
                const guideSummary = document.createElement('summary');
                guideSummary.textContent = `Contexto UNSA aplicado (${data.case_guides.length} casos guía)`;
                const guideList = document.createElement('div');
                for (const guide of data.case_guides) {
                    const card = document.createElement('section'); card.className = 'search-result';
                    const title = document.createElement('h4');
                    title.textContent = `${guide.code} — ${guide.title} · ${guide.area}`;
                    const scenario = document.createElement('p'); scenario.textContent = guide.scenario;
                    const focus = document.createElement('p'); focus.className = 'help';
                    focus.textContent = `Enfoque: ${guide.reasoning_focus}`;
                    card.append(title, scenario, focus); guideList.append(card);
                }
                guideDetails.append(guideSummary, guideList); article.append(guideDetails);
            }
            const details = document.createElement('details'), summary = document.createElement('summary');
            summary.textContent = `Ver ${data.evidence.length} disposiciones de evidencia`;
            const evidence = document.createElement('div');
            for (const item of data.evidence) {
                const card = document.createElement('section'); card.className = 'search-result';
                const title = document.createElement('h4');
                const kind = item.source_type === 'pims' ? ' · PROCEDIMIENTO SIMULADO'
                    : item.source_type === 'registros' ? ' · REGISTRO SIMULADO'
                    : item.source_type === 'fictitious_case' ? ' · CASO FICTICIO'
                    : item.source_type === 'reference' ? ' · REFERENCIA AUXILIAR' : '';
                title.textContent = `[${item.id}] ${item.source}${item.section ? ' — ' + item.section : ''}${kind}`;
                const score = document.createElement('p'); score.className = 'help'; score.textContent = `Similitud temática: ${Number(item.score).toFixed(3)}`;
                const excerpt = document.createElement('p'); excerpt.className = 'excerpt'; excerpt.textContent = item.excerpt;
                card.append(title, score, excerpt); evidence.append(card);
            }
            details.append(summary, evidence); article.append(details);
            const notice = document.createElement('p'); notice.className = 'guide-box'; notice.textContent = data.notice;
            article.append(notice);
        }
        $('conversation').append(article); article.scrollIntoView?.({behavior: 'smooth', block: 'start'});
    }

    function resetConversation() {
        conversationVersion++;
        history = []; $('conversation').replaceChildren(); $('caseText').value = '';
        const examples = {
            normativa: '¿Qué disposiciones respaldan el derecho de acceso?',
            pims: 'Ya se verificó la identidad. Para rectificar la fecha de nacimiento en matrícula, ¿a quién se deriva la solicitud?',
            registros: '¿Qué ocurrió en el expediente SIM-001?'
        };
        $('caseText').placeholder = examples[$('scope').value];
        message('assistant', 'Escribe una consulta sobre los documentos seleccionados.');
    }

    $('loginForm').addEventListener('submit', async event => {
        event.preventDefault(); key = $('apiKey').value;
        try {
            const [index, generator] = await Promise.all([api('/ai/status'), api('/agent/status')]);
            if (!index.ready) throw new Error(index.message);
            $('workspace').classList.remove('hidden'); $('loginForm').classList.add('hidden');
            $('logoutButton').classList.remove('hidden'); $('newChatButton').classList.remove('hidden');
            $('status').textContent = `Base lista: ${index.sources ?? index.documents} fuentes, ${index.provisions ?? index.chunks} disposiciones verificadas y ${index.case_guides ?? 0} casos guía UNSA.`;
            $('scope').value = index.pims_sources ? 'pims' : 'normativa';
            $('modelStatus').textContent = generator.message;
            $('apiKey').value = ''; resetConversation();
        } catch (error) { key = ''; $('status').textContent = error.message; }
    });

    $('scope').onchange = resetConversation;
    $('newChatButton').onclick = resetConversation;
    $('logoutButton').onclick = () => {
        conversationVersion++;
        key = ''; history = []; $('apiKey').value = ''; $('workspace').classList.add('hidden');
        $('conversation').replaceChildren(); $('loginForm').classList.remove('hidden');
        $('logoutButton').classList.add('hidden'); $('newChatButton').classList.add('hidden');
        $('status').textContent = 'Sesión cerrada.'; $('modelStatus').textContent = '';
    };

    $('caseForm').addEventListener('submit', async event => {
        event.preventDefault();
        const button = $('analyzeButton'), caseText = $('caseText').value.trim();
        if (!caseText) return;
        const version = conversationVersion;
        const prior = history.slice(-8); message('user', caseText); $('caseText').value = '';
        button.disabled = true; $('scope').disabled = true; $('status').textContent = 'Recuperando fuentes y generando conclusión…';
        try {
            const data = await api('/case-analysis', { method: 'POST', body: JSON.stringify({case: caseText, history: prior, scope: $('scope').value}) });
            if (version !== conversationVersion) return;
            message('assistant', data.answer, data);
            history.push({role: 'user', content: caseText}, {role: 'assistant', content: data.answer});
            history = history.slice(-8);
            $('status').textContent = data.mode === 'document_selection' ? 'Pasajes seleccionados y citados.' : data.mode === 'generative_rag' ? 'Respuesta fundamentada terminada.' : data.coverage === 'insufficient_evidence' ? 'Consulta sin cobertura documental.' : 'Fragmentos disponibles para revisión.';
        } catch (error) {
            if (version !== conversationVersion) return;
            message('assistant', `No se pudo completar el análisis: ${error.message}`);
            $('status').textContent = error.message;
        } finally { button.disabled = false; $('scope').disabled = false; $('caseText').focus(); }
    });
});
