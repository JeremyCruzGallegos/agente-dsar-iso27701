# Usar el proyecto con IA local

El asistente ayuda al DPO a encontrar documentos y revisar cada solicitud. Usa un modelo multilingüe de SentenceTransformers y FAISS en tu computadora. Muestra fragmentos y sus fuentes; el responsable revisa la información y decide la actuación.

## Iniciar en Linux Mint

Desde la carpeta del proyecto, detén el Flask anterior con Ctrl+C y ejecuta:

```bash
cd ~/Proyectos/agente-dsar
python3 iniciar.py --demo
```

El comando crea o reutiliza `.venv`, instala las dependencias necesarias, prepara configuración y tablas, descarga el modelo la primera vez, actualiza el índice y comprueba la IA con una búsqueda real. Luego inicia Flask y abre el panel DPO. La primera preparación requiere Internet y puede tardar. En los siguientes inicios reutiliza las dependencias y el modelo locales.

`--demo` agrega titulares ficticios sin borrar datos existentes. Omítelo para trabajar sin ejemplos. La clave DPO se muestra sólo en la terminal interactiva local: cópiala en el panel y pulsa Entrar al panel. También está en `backend/.env`; no se incluye en Git ni en la URL. La terminal debe permanecer abierta; Ctrl+C detiene el proyecto. Si el puerto 5000 está ocupado, detén la instancia anterior o usa `--port 5001`.

Si Python indica que falta `venv`, instala `sudo apt install python3-venv`. Si el navegador no se abre, utiliza http://127.0.0.1:5000/dpo. Para iniciar sin abrirlo automáticamente, añade `--no-browser`.

En Windows, desde la carpeta del proyecto:

```powershell
py -3.12 iniciar.py --demo
```

Este flujo local permite usar el portal y la IA antes de configurar n8n. Si ya tienes configurado el modo n8n, conserva esa configuración y mantén n8n encendido. Las instrucciones de n8n están en las guías de [Linux](CONFIGURAR_LINUX.md) y [Windows](CONFIGURAR_WINDOWS.md).

## Analizar casos con documentos de la UNSA

### Preparar el modelo que redacta conclusiones

El modelo de embeddings busca fragmentos, pero no redacta respuestas. Para activar el chat generativo local en Windows:

```powershell
winget install --id Ollama.Ollama --exact
ollama pull qwen2.5:1.5b
```

Ollama debe permanecer disponible en `http://127.0.0.1:11434`. Puedes cambiar el modelo o la dirección en `backend/.env`:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_TIMEOUT_SECONDS=120
LLM_CONTEXT_MAX_CHARS=12000
```

1. Coloca fuentes `.md` UTF-8 en la categoría correspondiente dentro de `ai_engine/documentos`.
2. Parte de [PLANTILLA_FUENTE.md](PLANTILLA_FUENTE.md) y completa todos sus metadatos. Para Markdown, usa encabezados claros (`#`, `##`, `###`): el agente conserva el encabezado como sección de la cita.
3. Valida antes de indexar: `python scripts/validate_documents.py`. Una fuente oficial incompleta, sin URL o en una categoría incorrecta será rechazada.
4. Detén el servidor y ejecuta `py -3.12 iniciar.py --solo-preparar` en Windows o `python3 iniciar.py --solo-preparar` en Linux.
5. Inicia normalmente y abre `http://127.0.0.1:5000/agente`.
6. Introduce los hechos y una pregunta concreta. El resultado presenta una respuesta preliminar y los fragmentos que la sustentan.

La consola expande conceptos jurídicos relevantes, recupera evidencia con FAISS y solicita a Ollama una conclusión en texto. El backend valida que los identificadores citados existan; si Ollama falla o inventa una cita, descarta la conclusión y conserva únicamente los fragmentos recuperados. Cuando existen fuentes normativas, los casos ficticios, formularios y resúmenes no se incluyen en el contexto usado para formular la conclusión. Las preguntas cortas reutilizan el último caso; una pregunta nueva y detallada inicia un contexto temático nuevo.

La conversación mantiene como máximo ocho mensajes en el navegador y se elimina al cerrar sesión o pulsar **Nueva conversación**. Las consultas y respuestas no se guardan en la bitácora; solo se registran metadatos operativos del análisis.

No mezcles versiones derogadas y vigentes sin identificarlas. Incluye título, entidad emisora, fecha, estado de vigencia y jerarquía cuando estén disponibles. Usa datos ficticios o anonimizados para los casos académicos.

## Atender una solicitud DSAR

1. Abre el portal del titular en http://127.0.0.1:5000 y registra una solicitud de prueba con ID `72839102`, correo `juan@example.com` y derecho Acceso.
2. En el panel DPO, abre Solicitudes y pulsa Revisar. Se carga el documento, los datos registrados y una orientación según el derecho solicitado.
3. Pulsa Buscar documentos con IA. La búsqueda queda limitada a documentos indexados que mencionan el ID seleccionado. Cada tarjeta muestra fuente, fragmento y similitud temática. El indicador IA lista confirma que el modelo y el índice se pudieron cargar.
4. Cambia la consulta o utiliza las sugerencias para encontrar información de contacto, publicidad o conservación. Puedes desmarcar el filtro del titular para una búsqueda general autorizada.
5. Para revisar un fragmento antes de entregar información, pulsa Revisar y ocultar datos de este fragmento y luego Ocultar coincidencias. Los nombres se añaden automáticamente si el titular está registrado. Revisa el resultado y los datos de terceros.
6. En Datos del titular consulta los datos, descarga el JSON portable o realiza la rectificación/supresión autorizada. Regresa a Solicitudes para guardar la nota, actualizar el estado y descargar la constancia PDF.

La similitud no es una probabilidad de certeza. El filtro encuentra documentos por una mención literal del ID: un documento puede mencionar más de una persona y debe revisarse. Si el ID no aparece en los documentos indexados, se muestra un resultado vacío, sin sustituirlo por documentos de otro titular. La recepción de una solicitud no da de alta automáticamente un titular en la base.

## Usar tus propios documentos

El corpus compartido se mantiene en Markdown UTF-8 validado dentro de `ai_engine/documentos`. Convierte previamente los PDF y verifica la transcripción contra la fuente oficial; el proyecto no incluye OCR. Para que una solicitud DSAR encuentre documentos individuales con el filtro activado, éstos deben mencionar su documento/ID completo, pero no deben subirse datos personales reales al repositorio.

Detén Flask y vuelve a ejecutar `python3 iniciar.py` para actualizar el índice. El modelo ya descargado se reutiliza. Una ruta de modelo local existente configurada en `EMBEDDING_MODEL` se conserva. También puedes comprobar la IA sin arrancar el portal:

```bash
python3 iniciar.py --solo-preparar
```

La búsqueda utiliza el índice local. Después de borrar o modificar documentos, vuelve a preparar el índice: la supresión SQL no borra archivos ni copias anteriores del índice. No se envían las consultas o los documentos a una API de IA externa. La primera descarga del modelo sí necesita acceso a Internet.

## Verificación y límites

Se verificaron el arranque, el estado autenticado de IA, una consulta con el modelo real y el filtro por ID. Las pruebas automatizadas cubren el panel guiado, renderizado seguro de fragmentos, resultados vacíos, fallos y limpieza al cerrar sesión. La autorización de actuaciones sigue a cargo del DPO. El ZIP del expediente y el envío por correo son funciones pendientes.
