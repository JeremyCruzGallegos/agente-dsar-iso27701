# Entrega 3 · resultados del ensayo de matrícula

**23 de noviembre de 2026.** La línea base `a9420a4` tenía 11 documentos y 38 apartados. Con los mismos documentos, la nueva carga conserva los 38 identificadores y agrega siete fichas Word. D30 pasa a v0.2 e incorpora una tabla propuesta de seguimiento. La nota de procedencia identifica archivo, versión, plantilla declarada y ubicación.

**Suite local.** Pasaron 107 pruebas del backend y 8 de interfaz. Pytest usa una base aislada y las pruebas de selección que sustituyen al modelo comprueban el contrato de citas. La suite de interfaz usa DOM automatizado, incluye pruebas con respuestas simuladas y un recorrido contra Flask. Separadamente se ejecutó el recorrido siguiente en Edge 158, Python 3.14.2, PostgreSQL 19 y Ollama con Qwen 2.5 1.5B, sin simular respuestas HTTP. Se usó PostgreSQL nativo porque el motor local de Docker Desktop estaba detenido.

| Caso | Resultado esperado | Observado | Evidencia |
|---|---|---|---|
| A · referencias de curso | D30 identifica 7.2, 7.3 y A.3.17 con ubicación en el Word | El chat mostró el párrafo anterior al §1 con atribución a la guía del curso, en respaldo documental. Las pruebas cubren también D11 (7.5.1–7.5.3) y D34 (10.2) | [Consultas reales](evidencias-entrega3/interfaz.json), [regresión](../../backend/tests/test_pims.py) |
| B · tabla | Recuperar desde la base el dato exclusivo de la celda y su apartado | El modelo seleccionó la fila de «Refuerzo pendiente», D30 §3, tabla 1, fila 2. En una copia de prueba, cambiar la celda permitió recuperar un texto centinela nuevo | [Word](plantillas/D30.docx), [consulta](evidencias-entrega3/interfaz.json) |
| C · comparación | Dar una fila por código con los valores de ambas matrices | R01 pasó de índice inicial 6 a meta 4, R02 de 5 a meta 3 y R03 de 4 a meta 3. Las tres aceptaciones están pendientes del propietario. Seis citas remiten a las dos matrices; la regresión cambia el orden, modifica un valor en la base aislada y pide además un código ausente | [Filas y citas](evidencias-entrega3/interfaz.json), [regresión](../../backend/tests/test_pims.py) |
| D · plazo | Identificar el dato ausente sin atribuir días al procedimiento | Cobertura parcial en D20. Una prueba adicional incorpora 12 días hábiles ficticios exclusivamente en la base de prueba y recupera el valor introducido | [Consulta](evidencias-entrega3/interfaz.json), [regresión](../../backend/tests/test_pims.py) |
| E · identidad | Derivación según §3 o subsanación según §2 | En el recorrido final Ollama seleccionó D20 §3 con identidad verificada. Con acreditación pendiente el chat mostró el respaldo D20 §2. Durante el desarrollo se detectó una selección secundaria incorrecta para el segundo caso y se agregó una prueba que descarta ese resultado | [Modos, respuestas y citas](evidencias-entrega3/interfaz.json) |
| F · oposición | Ticket recibido, revisión humana documentable, trazabilidad y constancia | Edge registró DSAR-2AA7F677, lo filtró en el DPO y recorrió verificación, proceso y cierre con decisión de ensayo. El PDF contiene el ticket, Oposición y Completado. La prueba de backend verifica que el titular sigue activo y el cierre exige motivo. La decisión del ensayo se introdujo por automatización del panel | [Constancia](evidencias-entrega3/oposicion.pdf), [bitácora y nota](evidencias-entrega3/interfaz.json), [regresión](../../backend/tests/test_oposicion.py) |
| G · actualización | Preservar los ID y el ticket de una base anterior, sin duplicados ni importación parcial | PostgreSQL partió del código anterior; conservó el ticket histórico, los 38 ID y los 45 ID tras repetir la carga. Una prueba de transacción retira un editable justo después de cambiar otro, comprueba la reversión y conserva una fuente externa | [Migración real](evidencias-entrega3/importacion.json), [rollback en SQLite](../../backend/tests/test_pims.py) |
| H · alcance y caída del modelo | Mostrar evidencia insuficiente o identificar el respaldo | La pregunta sobre satélites quedó sin evidencia. Una segunda instancia del chat conectada a la misma base y a un puerto Ollama sin servicio mostró D30 con el indicador documental. El ensayo mantuvo disponible la instancia de Ollama del equipo | [Indicadores de la interfaz](evidencias-entrega3/interfaz.json) |

El flujo probado de oposición fue de entrada directa. El workflow opcional de n8n reenvía el cuerpo y la clave de idempotencia a Flask. No se ejecutó un webhook publicado para oposición. El esquema histórico de tickets usa `VARCHAR(20)` sin enum nativo ni restricción de lista, por lo que admite el nuevo tipo sin reescritura. Al importar sobre la versión previa se crea la tabla de procedencia `pims_origins` y se completa dentro de la transacción de importación.

## Repetir en Windows

Desde la raíz del repositorio, con Python 3.14, Node compatible con `package.json`, Edge, los binarios de PostgreSQL y Ollama disponibles:

```powershell
py -0p
if (!(Test-Path .venv\Scripts\python.exe)) { py -3.14 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
# Si se usó el Node portátil de esta laptop, agréguelo a esta terminal:
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    $nodeDemo = Get-ChildItem "$env:TEMP/pims-node-*/node*/node.exe" | Select-Object -First 1
    if ($nodeDemo) { $env:Path = $nodeDemo.DirectoryName + ';' + $env:Path }
}
npm.cmd ci
$env:PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
& $env:PYTHON -m pytest backend/tests -q
npm.cmd test
ollama list
ollama pull qwen2.5:1.5b
& $env:PYTHON scripts/demo_entrega3.py --pg-bin 'C:/Program Files/PostgreSQL/19/bin' --salida "$env:TEMP/entrega3-resultados"
```

El último comando usa puertos locales disponibles, claves temporales y una base nueva creada con el código de `a9420a4`. Ejecuta Edge sin ventana, conserva los resultados en la carpeta de salida y detiene sus servidores. Cada ejecución genera otro ticket ficticio. Los modos del modelo pueden variar; la prueba contrasta la fuente y el apartado.

Para mostrar la cadena sobre la base de demostración habitual, arranca el proyecto según la [guía](README.md). En pgAdmin, abre la base configurada por el proyecto y ejecuta:

```sql
SELECT s.code, o.version, s.notes AS clase, o.template AS plantilla,
       o.file AS editable, o.locator, p.id, p.provision_code, p.content
FROM pims_origins o
JOIN legal_provisions p ON p.id = o.provision_id
JOIN legal_sources s ON s.id = p.source_id
WHERE s.code = 'PIMS-SIM-D30'
ORDER BY p.sort_order;
```

Coteja la ficha y §3 con el Word y con las citas del navegador. Para enseñar qué requiere participación de los grupos, abre la [minuta y matriz de seguimiento](coordinacion-entrega3.md). La corrida técnica demuestra importación, consulta y tramitación simulada. La aprobación de roles, canales, plazos, riesgos, plantillas y eficacia sigue pendiente de evidencia del equipo.
