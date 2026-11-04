# Inicio rápido

```powershell
docker compose up -d postgres
py -3.12 iniciar.py --demo
ollama pull qwen2.5:3b
```

Después registra fuentes y disposiciones con la guía [Base de datos normativa](BASE_DE_DATOS_NORMATIVA.md).
El chat está en `http://127.0.0.1:5000/agente`. PostgreSQL conserva el corpus y Ollama genera la
conclusión; no se usan archivos documentales ni índices FAISS.

Pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
$env:PYTHON=(Resolve-Path '.venv\Scripts\python.exe').Path
npm test
```
