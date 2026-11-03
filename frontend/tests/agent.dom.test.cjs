const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require(process.env.DSAR_JSDOM_MODULE || 'jsdom');

const root = path.resolve(__dirname, '../..');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(check) {
    for (let i = 0; i < 100; i++) { if (check()) return; await delay(5); }
    throw new Error('La interfaz no alcanzó el estado esperado.');
}

test('agente mantiene historial, muestra citas y limpia la conversación', async () => {
    const html = fs.readFileSync(path.join(root, 'frontend', 'agent.html'), 'utf8');
    const dom = new JSDOM(html, {url: 'http://127.0.0.1:5000', runScripts: 'outside-only'});
    const window = dom.window, payloads = [];
    window.HTMLElement.prototype.scrollIntoView = () => {};
    window.fetch = async (url, options = {}) => {
        if (url === '/api/ai/status') return {ok:true, json:async()=>({data:{ready:true,documents:3,chunks:9}})};
        if (url === '/api/agent/status') return {ok:true, json:async()=>({data:{ready:true,model:'test',message:'Modelo listo.'}})};
        if (url === '/api/case-analysis') {
            payloads.push(JSON.parse(options.body));
            return {ok:true, json:async()=>({data:{answer:'Conclusión fundada [1].',mode:'generative_rag',model:'test',confidence:'media',limitations:[],notice:'Revisar.',evidence:[{id:1,source:'legislacion/norma.md',section:'Artículo 1',source_type:'normative',score:.8,excerpt:'Texto'}]}})};
        }
        throw new Error('URL inesperada: ' + url);
    };
    window.eval(fs.readFileSync(path.join(root, 'frontend', 'agent.js'), 'utf8'));
    window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
    const $ = id => window.document.getElementById(id);
    $('apiKey').value = 'clave'; $('loginForm').dispatchEvent(new window.Event('submit', {cancelable:true}));
    await until(() => !$('workspace').classList.contains('hidden'));

    $('caseText').value = 'Primer caso'; $('caseForm').dispatchEvent(new window.Event('submit', {cancelable:true}));
    await until(() => payloads.length === 1 && !$('analyzeButton').disabled);
    assert.deepEqual(payloads[0].history, []);
    assert.match($('conversation').textContent, /Conclusión fundada \[1\]/);

    $('caseText').value = 'Pregunta de seguimiento'; $('caseForm').dispatchEvent(new window.Event('submit', {cancelable:true}));
    await until(() => payloads.length === 2 && !$('analyzeButton').disabled);
    assert.equal(payloads[1].history.length, 2);
    assert.equal(payloads[1].history[0].content, 'Primer caso');

    $('newChatButton').click();
    assert.doesNotMatch($('conversation').textContent, /Primer caso/);
    dom.window.close();
});
