# Demostración del PIMS de matrícula

El equipo puede atender un caso de rectificación y verificar, en pantalla, la sección que respalda la orientación del agente. El escenario, los roles, los expedientes y la valoración de riesgos corresponden a una implementación universitaria simulada. La identificación de cláusulas y controles sigue la Guía de implementación y trazabilidad, revisión 2, y el diagrama compartidos en el curso.

## Arranque en Windows

Abre PowerShell en la carpeta del proyecto con Docker Desktop iniciado. El lanzador admite Python 3.11 o posterior. Usa un intérprete instalado según `py -0p`. Para seleccionar Python 3.14, por ejemplo, usa `py -3.14 iniciar.py --demo`.

```powershell
if (!(Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
docker compose up -d postgres
ollama pull qwen2.5:1.5b
py iniciar.py --demo
```

Ollama debe estar en ejecución para seleccionar pasajes con IA. En equipos sin el servicio, la interfaz muestra los fragmentos recuperados. Abre `http://127.0.0.1:5000/agente` y usa la clave DPO generada en `backend/.env`. La clave se introduce únicamente en la sesión local.

## Demostración de cinco minutos

1. Selecciona **Procedimientos y planes del PIMS simulado**. Pregunta «Ya se verificó la identidad. Para rectificar la fecha de nacimiento en matrícula, ¿a quién se deriva y qué registra el operador?». Abre la evidencia. D20 §3 identifica al responsable funcional y el registro de destinatario, fecha y estado.
2. Abre una conversación nueva. Pregunta «La acreditación de identidad está pendiente. ¿Qué hace el operador de recepción?». Contrasta con D20 §2. El operador comunica qué falta y mantiene el expediente pendiente.
3. Cambia a **Registros y matrices del ejercicio**. Pregunta «¿Qué ocurrió en SIM-001 con la rectificación de matrícula?». Muestra la actuación y su referencia en el expediente ficticio.
4. En una conversación nueva del PIMS pregunta «¿Cuántos satélites orbitan Júpiter?». La falta de evidencia queda visible.
5. En el panel DPO, consulta los apartados por ámbito y conserva el código y la sección en la nota de resolución del ticket al tramitar el caso. El expediente SIM-001 es un registro de escritorio. El caso de fecha de nacimiento sirve para orientación documental; los campos de rectificación que admite el portal son nombre y correo.

## Correspondencia de los editables con el ejercicio

| Archivo | Plantilla docente y uso en matrícula | Referencia de la guía |
|---|---|---|
| D11.docx | Control de documentos y registros, revisión de copias y retirada de versiones | 7.5.1–7.5.3 |
| D12.docx | Metodología de evaluación y tratamiento, consecuencias para titulares y universidad | 6.1.2 y 6.1.3 |
| D13.xlsx | Apéndice 1, evaluación de R01, R02 y R03 | 6.1.2 y 8.2 |
| D15-MAT.xlsx | Apéndice 2, tratamientos y niveles residuales previstos | 6.1.3 y 8.3 |
| D13-INF.docx | Apéndice 3, informe del ejercicio y decisiones pendientes | 8.2 y 8.3 |
| D15-PLAN.docx | Plan de tratamiento, responsables, recursos, semanas y verificación | 6.1.3 f–g y 8.3 |
| D30.docx | Capacitación y concienciación por función, ejercicios y criterios de logro | 7.2, 7.3 y A.3.17 |
| D34.docx | Procedimiento para medidas correctivas y revisión de eficacia | 10.2 |
| D34-AC01.docx | Formulario completado sobre una constancia pendiente | 10.2 |
| D20.md | Procedimiento local del ejercicio de derechos y consulta sobre automatización | A.1.3.7, A.1.3.10 y A.1.3.11 según aplicabilidad |
| D20-caso-rectificacion.md | Registro ficticio SIM-001 de recepción, derivación y cierre | Evidencia del procedimiento D20 |

Las nueve adaptaciones tienen redacción y maquetación propias. El catálogo identifica la plantilla original de cada una. Los códigos D corresponden a la organización del material del curso.

## Actualizar y comprobar los documentos

Edita la copia de trabajo que identifica `catalogo.json`. Conserva los apartados numerados en Word y Markdown y el identificador de cada riesgo en Excel. Guarda las matrices con sus fórmulas recalculadas. Actualiza versión y referencias si cambia el procedimiento. Desde la raíz, con el entorno del proyecto activo, ejecuta:

```powershell
.\.venv\Scripts\python.exe -m flask --app app import-pims
```

La carga actualiza las secciones por código dentro de una transacción. La consulta del chat utiliza las secciones de la base. El indicador de verificación en estas fuentes identifica texto cotejable contra el archivo de simulación. La revisión del equipo y la aprobación institucional son procesos distintos.

## Evidencia y coordinación pendientes

El archivo `prueba-integracion.json` guarda consultas, respuestas, modo de ejecución, fuentes y apartados devueltos en una ejecución de la interfaz con DOM automatizado, Flask, PostgreSQL 16.2 y Ollama con Qwen 2.5 1.5B. También se ejecutó una rectificación de correo con un titular ficticio, consulta del D20 desde la API del panel, cambio de correo y cierre del ticket. La constancia emitida por el sistema es [constancia-rectificacion.pdf](constancia-rectificacion.pdf). Las pruebas unitarias incluyen rutas sin modelo. El chat no cambia por sí mismo el expediente del titular.

| Acuerdo que debe cerrar el equipo | Con quién contrastarlo | Evidencia para la entrega |
|---|---|---|
| Alcance y equivalencias de los roles propuestos en D20 | Grupos de alcance y gobierno | Acta breve con rol, responsable, fecha y edición revisada |
| Tratamiento de matrícula, canal y plazos aplicables a cada derecho | Grupos de inventario y requisitos | Identificador del tratamiento y referencia verificable para cada plazo |
| Riesgos R01–R03 y selección de controles | Grupo de riesgos y Declaración de Aplicabilidad | Decisión del propietario sobre las medidas y el residual, con evidencia de eficacia |
| Ediciones compartidas y prueba de capacitación | Custodio documental y equipo que hará la exposición | Revisión cruzada, resultado del ejercicio y registro de cambios |

Referencia de edición: [ISO/IEC 27701:2025](https://www.iso.org/standard/27701).
