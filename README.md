# Agente de Derechos del Titular (DSAR) - ISO/IEC 27701

Proyecto académico para la automatización de Solicitudes de Derechos de los Titulares (*Data Subject Access Requests*) alineado con la norma **ISO/IEC 27701** utilizando una arquitectura basada en **Privacy by Design**.

## 🛠️ Stack Tecnológico
* **Frontend:** HTML5, CSS3, JavaScript puro (Vanilla JS).
* **Backend Core:** Python 3.11+, Flask API REST.
* **Motor de IA & Vectores:** FAISS (Facebook AI Similarity Search) + Modelo Local de Embeddings (`SentenceTransformers`).
* **Orquestación & Workflows:** n8n (Webhooks y procesamiento automatizado).
* **Asistencia de IA:** Astra AI en VS Code.

## 👥 Equipo y Distribución de Roles
* **Integrante 1:** Módulo Frontend (Portal del Usuario, Panel DPO y conexión Fetch).
* **Integrante 2:** Módulo Backend (API REST en Flask, Base de Datos SQL y Reglas de Retención).
* **Integrante 3:** Módulo de IA (Indexación semántica en FAISS y Embeddings locales).
* **Integrante 4:** Orquestación en n8n, Anonimización PII, Reportes PDF e Integración con Astra AI (VS Code).

## 📂 Estructura del Proyecto
agente-dsar-iso27701/
├── frontend/          # Vistas HTML, CSS y cliente Vanilla JS (Integrante 1)
├── backend/           # API Flask y modelos de BD relacional (Integrante 2)
├── ai_engine/         # Script de FAISS y modelo local de embeddings (Integrante 3)
├── static/            # Enlace a frontend/: Flask publica estos archivos sin duplicarlos
├── app.py             # Inicio de Flask desde la raíz
├── n8n_workflows/     # Flujos de trabajo exportados de n8n en JSON (Integrante 4)
├── .gitignore
└── README.md

##  Instrucciones de Ejecución
1. Clonar el repositorio: `git clone https://github.com/Ypss8522/agente-dsar-iso27701.git`
2. Preparar las dependencias y variables como se indica abajo.
3. Levantar Flask: `python app.py` (también funciona `python backend/app.py`).
4. Iniciar n8n localmente en el puerto 5678: `npx n8n`.
5. Abrir `http://localhost:5000`; el panel DPO está en `/dpo`.

## Preparación del backend y del modelo local

Desde la raíz del repositorio, con Python 3.11+ y soporte para pip/venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt -r ai_engine/requirements.txt
```

Configurar `SERVICE_API_KEY`, `DPO_API_KEY` y `AUDIT_HASH_KEY` con valores propios en las variables de entorno o en `backend/.env` (ignorado por Git). El backend exige `X-API-Key` en sus rutas de datos y de búsqueda. Las claves de servicio permanecen en n8n, nunca en el JS del navegador.

Preparar una vez el modelo multilingüe ya elegido por el equipo (requiere Internet):

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2').save('models_local/embeddings')"
export EMBEDDING_MODEL="$PWD/models_local/embeddings"
python -m ai_engine.search_engine
python -m flask --app app init-db
python app.py
```

El motor lee los PDF/TXT de `ai_engine/documentos/`, divide el contenido en chunks, normaliza embeddings y construye `IndexFlatIP` para similitud coseno. Las búsquedas usan `local_files_only=True` y CPU. El modelo y el índice deben estar preparados antes de consultar; no se construye el índice ni se descarga el modelo desde una petición HTTP. Si ya tenías un índice, reconstruirlo: ahora los metadatos incluyen el modelo para detectar incompatibilidades. Reiniciar Flask después de reconstruirlo. Los índices y modelos generados quedan excluidos de Git.

## API Flask → FAISS

`GET /api/user-data?user_id=72839102` conserva la consulta SQL, autenticación y auditoría existentes.

`POST /api/vector-search` requiere `Content-Type: application/json` y `X-API-Key` con una clave de servicio o DPO. El servicio adaptador está en `backend/dsar_api/services/search_engine.py` y llama al motor existente de `ai_engine/search_engine.py`:

```json
{"query":"correo electrónico de Juan Pérez","k":5}
```

Respuesta de ejemplo (score ilustrativo):

```json
{"status":"success","data":{"results":[{"texto":"Texto del documento","fuente":"demo.txt","score":0.8}],"count":1,"metric":"cosine_similarity"}}
```

Un score mayor indica más proximidad semántica. `k` admite enteros entre 1 y 50 y se limita al tamaño del índice. El endpoint devuelve JSON uniforme: 401 sin clave válida, 422 para entradas inválidas, 400 para JSON mal formado, 415 sin el tipo de contenido correcto, 503 si falta el modelo/índice y 500 ante un fallo inesperado del motor. La auditoría registra el número de resultados y `k`, sin guardar la consulta ni los textos. La similitud no demuestra que un documento pertenezca al titular ni sustituye la revisión de PII.

## Frontend → n8n

El formulario envía JSON mediante POST a `http://localhost:5678/webhook/dsar-request` con `user_id`, `email`, `request_type`, `details` y `timestamp`. Los tipos se mantienen compatibles con el backend: `Acceso`, `Supresion`, `Rectificacion`, `Portabilidad`. La URL se puede cambiar con `data-webhook-url` en `frontend/index.html`.

En n8n:

1. Crear el nodo Webhook con método POST y ruta `dsar-request`, y activar el flujo para usar la URL de producción `/webhook/`.
2. Permitir en **Allowed Origins (CORS)** el origen del formulario, por ejemplo `http://localhost:5000`.
3. Enviar los campos recibidos en `$json.body` a `POST http://localhost:5000/api/requests`, usando `X-API-Key` configurado en n8n. Si n8n corre en Docker, usar el hostname accesible del backend desde el contenedor.
4. Configurar **Respond to Webhook** y responder únicamente después de crear el ticket, copiando el ticket real de `data.ticket_id` de Flask al campo superior `ticket_id`:

```json
{"status":"success","ticket_id":"DSAR-XXXXXXXX"}
```

Propagar también los errores de Flask. El frontend comprueba HTTP, JSON y ticket, impide envíos simultáneos y espera hasta 15 segundos. Ante errores conserva el formulario y no genera tickets ficticios. Después de un timeout o una respuesta sin ticket, comprobar en n8n si ya se creó la solicitud antes de reenviarla. CORS de Flask y del Webhook se configuran por separado. `CORS_ORIGINS` admite una lista de orígenes separados por comas.

## Pruebas

```bash
python -m pytest backend/tests -q
python -m unittest ai_engine.test_search_engine -v
node frontend/tests/main.test.cjs
python -m compileall -q app.py backend ai_engine
node --check frontend/main.js
```

Las pruebas del backend requieren sus dependencias. La prueba de FAISS usa NumPy/FAISS reales con un encoder determinista; se omite explícitamente si no están instalados. No descarga el modelo. La verificación con SentenceTransformers real requiere preparar el modelo/índice y llamar a la API; la integración completa con n8n requiere que el flujo esté activo.

Verificación de esta integración: pasaron 4 pruebas de validación/búsqueda exacta y 4 pruebas JavaScript, además de las comprobaciones de sintaxis Python/JS y `git diff --check`. La prueba con FAISS real quedó omitida por falta de FAISS/NumPy; las pruebas del backend no pudieron ejecutarse porque el entorno no tiene pytest ni sus dependencias. Queda pendiente la verificación completa después de instalarlas y preparar el modelo y n8n.
