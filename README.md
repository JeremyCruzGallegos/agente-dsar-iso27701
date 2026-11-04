# Agente normativo y de derechos — ISO/IEC 27001/27701

Proyecto académico para analizar casos de derechos y privacidad en el contexto universitario.
El contexto del agente se almacena de forma estructurada en PostgreSQL; no lee PDF, TXT ni
Markdown. Ollama redacta la conclusión exclusivamente a partir de artículos y cláusulas
verificados recuperados de la base.

ISO/IEC 27001 no es una ley. Las leyes peruanas, reglamentos, normas institucionales UNSA y
cláusulas ISO autorizadas se registran como fuentes distintas, conservando entidad emisora,
vigencia, URL oficial y unidad normativa.

## Arquitectura

```text
PostgreSQL
  legal_sources       ley, reglamento, ISO o norma UNSA
  legal_provisions    artículo o cláusula verificable
  legal_relations     vínculos entre disposiciones
        │
        ▼
recuperación SQL ponderada → evidencia numerada → Ollama → conclusión con citas
```

El proyecto también contiene el módulo DSAR para registrar y gestionar solicitudes de acceso,
rectificación, cancelación/supresión, oposición y portabilidad.

## Inicio recomendado

Requisitos: Python 3.11+, Docker Desktop y Ollama.

```powershell
docker compose up -d postgres
py -3.12 iniciar.py --demo
```

Para habilitar conclusiones generativas:

```powershell
winget install --id Ollama.Ollama --exact
ollama pull qwen2.5:3b
```

Abre:

- `http://127.0.0.1:5000/agente`: chat normativo.
- `http://127.0.0.1:5000/solicitudes`: portal del titular.
- `http://127.0.0.1:5000/dpo`: panel de gestión.

La base normativa empieza vacía. Sigue [Base de datos normativa](docs/BASE_DE_DATOS_NORMATIVA.md)
para registrar fuentes y artículos mediante la API. No es necesario reconstruir un índice.

## Controles de calidad

- Solo se recuperan fuentes `active` y disposiciones `verified=true`.
- Las citas se validan contra la evidencia recuperada.
- Las fuentes tienen código único y cada artículo es único dentro de su fuente.
- Una falla de Ollama conserva la evidencia pero no inventa una conclusión.
- La bitácora guarda metadatos, no el texto de las consultas.
- El resultado es académico y requiere revisión humana de vigencia y jerarquía.

## API del conocimiento

| Ruta | Rol | Uso |
| --- | --- | --- |
| GET `/api/knowledge/status` | Servicio / DPO | Recuento de fuentes y disposiciones verificadas |
| GET `/api/knowledge/sources` | Servicio / DPO | Lista de fuentes |
| POST `/api/knowledge/sources` | DPO | Registra una fuente |
| GET `/api/knowledge/sources/<id>` | Servicio / DPO | Fuente con sus disposiciones |
| POST `/api/knowledge/sources/<id>/provisions` | DPO | Registra un artículo o cláusula |
| PATCH `/api/knowledge/provisions/<id>` | DPO | Corrige o verifica una disposición |
| POST `/api/vector-search` | Servicio / DPO | Recuperación normativa ponderada |
| POST `/api/case-analysis` | Servicio / DPO | Análisis con evidencia y conclusión local |
| GET `/api/agent/status` | DPO | Estado de Ollama |

Las rutas privadas usan `X-API-Key`. Las claves se generan en `backend/.env`, archivo excluido de Git.

## Estructura

```text
backend/       API, modelos SQL, servicios y pruebas
database/      DDL PostgreSQL del corpus normativo
frontend/      Chat, portal y panel DPO
skills/        Skill de análisis normativo trazable
scripts/       Inicialización, comprobación y diagnóstico
docs/          Guías del proyecto
compose.yaml   PostgreSQL local persistente
```

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
$env:PYTHON=(Resolve-Path '.venv\Scripts\python.exe').Path
npm test
```

Este proyecto no sustituye asesoría legal, una decisión administrativa ni una certificación ISO.
