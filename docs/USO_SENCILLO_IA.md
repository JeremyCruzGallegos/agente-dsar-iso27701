# Usar el agente con PostgreSQL y Ollama

El agente utiliza dos componentes distintos:

- PostgreSQL conserva fuentes, artículos, cláusulas, vigencia y verificación.
- Ollama redacta una conclusión usando únicamente las disposiciones recuperadas.

No se leen ni indexan PDF, TXT o Markdown.

## Primera ejecución en Windows

Desde la raíz del proyecto:

```powershell
docker compose up -d postgres
py -3.12 iniciar.py --demo
```

El comando crea `.venv`, instala dependencias, genera las claves locales, crea las tablas y abre
el proyecto. `--demo` agrega titulares ficticios para probar el módulo DSAR, pero no inventa normas.

Si `backend/.env` ya existía con SQLite, reemplaza su `DATABASE_URL` por:

```env
DATABASE_URL=postgresql+psycopg://dsar:dsar_local@127.0.0.1:5432/dsar_agent
```

## Preparar Ollama

```powershell
winget install --id Ollama.Ollama --exact
ollama pull qwen2.5:3b
```

Sin Ollama puedes comprobar la recuperación y las evidencias, pero no se genera una conclusión.

## Cargar el contexto

Consulta [BASE_DE_DATOS_NORMATIVA.md](BASE_DE_DATOS_NORMATIVA.md). El flujo es:

1. Registrar una fuente oficial en `legal_sources`.
2. Dividirla por artículos o cláusulas en `legal_provisions`.
3. Revisar texto, código, URL y vigencia.
4. Marcar cada disposición revisada con `verified=true`.
5. Consultar `/api/knowledge/status` y probar el chat.

No pegues una norma completa en un solo registro y no incluyas interpretación dentro de `content`.
Las disposiciones nuevas se encuentran inmediatamente; no existe un índice que reconstruir.

## Probar el agente

Abre `http://127.0.0.1:5000/agente` y pregunta, por ejemplo:

```text
Un estudiante solicita acceso a sus datos personales almacenados en una plataforma educativa.
¿Qué debe revisar la universidad?
```

La respuesta debe mostrar evidencia con código de fuente y artículo. Si la base no contiene una
disposición pertinente, el agente debe indicar evidencia insuficiente en vez de completar el vacío
con conocimiento general.

## Verificación técnica

```powershell
.\.venv\Scripts\python.exe scripts\check_ai.py
.\.venv\Scripts\python.exe -m pytest backend\tests -q
$env:PYTHON=(Resolve-Path '.venv\Scripts\python.exe').Path
npm test
```

El chat conserva hasta ocho mensajes en el navegador. El análisis es académico: antes de tomar una
decisión deben comprobarse la fuente oficial, su vigencia, jerarquía y aplicación al caso concreto.
