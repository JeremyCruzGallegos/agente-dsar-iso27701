// Recorrido de Edge sobre páginas servidas por Flask. El lanzador crea la base aislada.
const { chromium } = require('playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const [online, offline, output] = process.argv.slice(2);

async function main() {
    const browser = await chromium.launch({channel: 'msedge', headless: true});
    try {
        const page = await browser.newPage();
        const findings = {browser: browser.version(), consultas: []};
        async function login(url, route) {
            await page.goto(url + route);
            await page.locator('#apiKey').fill(process.env.DPO_API_KEY);
            await page.locator('#loginForm button').click();
            await page.locator('#workspace').waitFor();
        }
        async function ask(scope, question) {
            await page.locator('#newChatButton').click();
            await page.locator('#scope').selectOption(scope);
            await page.locator('#caseText').fill(question);
            const response = page.waitForResponse(r => r.url().endsWith('/api/case-analysis'), {timeout: 260000});
            await page.locator('#analyzeButton').click();
            const data = (await (await response).json()).data;
            const message = page.locator('#conversation article.assistant').last();
            await message.locator('details').first().waitFor();
            assert.equal(await message.locator('.chat-text').innerText(), data.answer);
            const sources = data.citations.map(id => {
                const row = data.evidence.find(item => item.id === id);
                return {id, documento: row.source, apartado: row.section, origen: row.origin};
            });
            findings.consultas.push({question, mode:data.mode, model:data.model, coverage:data.coverage,
                answer:data.answer, fuentes:sources, indicador:await message.locator('.help').first().textContent()});
            console.log(scope, data.mode, sources.map(s => s.documento.split(' — ')[0] + ' §' + s.apartado.split(' — ')[0]).join(', ') || data.coverage);
            return data;
        }
        await login(online, '/agente');
        const ref = await ask('pims', '¿Qué cláusulas o controles cita el plan de capacitación D30?');
        assert.match(ref.answer, /7\.2, 7\.3 y A\.3\.17/);
        const table = await ask('pims', 'D30: ¿qué criterio de seguimiento se propone para el refuerzo pendiente en la tabla?');
        assert.match(table.answer, /segunda constancia simulada/);
        const risks = await ask('registros', 'Compara los índices iniciales y residuales de R01, R02 y R03');
        assert.equal(risks.mode, 'document_comparison');
        assert.equal(risks.citations.length, 6);
        const deadline = await ask('pims', '¿Cuál es el plazo legal exacto en días hábiles para rectificar matrícula?');
        assert.equal(deadline.coverage, 'partial');
        for (const [question, section] of [
            ['Ya se verificó la identidad. Para rectificar la fecha de nacimiento en matrícula, ¿a quién se deriva y qué registra el operador?', '3'],
            ['La acreditación de identidad está pendiente. ¿Qué hace el operador de recepción?', '2']]) {
            const answer = await ask('pims', question);
            assert.equal(answer.evidence[0].record_code, section);
            assert(answer.citations.some(id => answer.evidence[id-1].record_code === section));
        }
        assert(findings.consultas.some(result => result.mode === 'document_selection'));
        assert.equal((await ask('pims', '¿Cuántos satélites orbitan Júpiter?')).coverage, 'insufficient_evidence');
        await login(offline, '/agente');
        const backup = await ask('pims', '¿Qué referencias cita D30?');
        assert.equal(backup.mode, 'retrieval_only');
        assert.match(findings.consultas.at(-1).indicador, /documental/);

        await page.goto(online + '/solicitudes');
        await page.locator('#userId').fill('72839102');
        await page.locator('#email').fill('ensayo@example.invalid');
        await page.locator('#requestType').selectOption('Oposicion');
        await page.locator('#details').fill('Ejercicio ficticio: oposición al uso complementario de matrícula.');
        await page.locator('#btnSubmit').click();
        await page.locator('#responseCard').waitFor();
        const ticket = await page.locator('#ticketId').innerText();
        assert.match(ticket, /^DSAR-[A-F0-9]{8}$/);
        await login(online, '/dpo');
        await page.locator('#typeFilter').selectOption('Oposicion');
        await page.locator('#filterForm button').click();
        const row = page.locator('tr').filter({hasText: ticket});
        await row.getByText('Revisar').click();
        await page.locator('#requestDetail').waitFor();
        assert.match(await page.locator('#caseSummary').innerText(), /Oposición.*Recibido/);
        const note = 'Simulación D20 §7: se admite la oposición al uso complementario de matrícula. Se mantiene el registro principal.';
        for (const status of ['En verificacion', 'En proceso', 'Completado']) {
            await page.locator('#newStatus').selectOption(status);
            if (status === 'Completado') await page.locator('#resolutionNote').fill(note);
            await page.locator('#saveStatus').click();
            await page.waitForFunction(s => document.querySelector('#caseSummary').textContent.endsWith(s), status);
        }
        assert.equal(await page.locator('#resolutionNote').inputValue(), note);
        const download = page.waitForEvent('download');
        await row.getByText('PDF').click();
        await (await download).saveAs(path.join(output, 'oposicion.pdf'));
        findings.oposicion = {ticket, decision_simulada:note, estado:'Completado',
            historial:await page.locator('#auditEntries').textContent()};
        fs.writeFileSync(path.join(output, 'interfaz.json'), JSON.stringify(findings,null,2)+'\n');
    } finally { await browser.close(); }
}
main().catch(error => {console.error(error); process.exitCode = 1;});
