# Base de datos normativa del agente

El agente ya no lee PDF, TXT ni Markdown. Su contexto procede de PostgreSQL y se organiza así:

- `legal_sources`: identifica la ley, reglamento, estándar ISO, norma institucional o jurisprudencia.
- `legal_provisions`: guarda cada artículo, cláusula o disposición como una unidad consultable.
- `legal_relations`: relaciona disposiciones que implementan, complementan, modifican o contradicen otras.

Solo participan en las respuestas las fuentes con `status = active` y las disposiciones con
`verified = true`. No guardes una norma completa en un único registro: crea una disposición por
artículo o cláusula para que la recuperación y las citas sean precisas.

## 1. Iniciar PostgreSQL

Con Docker Desktop instalado, desde la raíz del proyecto:

```powershell
docker compose up -d postgres
```

Copia `backend/.env.example` como `backend/.env` y conserva esta conexión:

```env
DATABASE_URL=postgresql+psycopg://dsar:dsar_local@127.0.0.1:5432/dsar_agent
```

Después ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts\setup.py
```

También está disponible el DDL independiente en `database/schema.sql`.

## 2. Registrar una fuente

Usa la clave `DPO_API_KEY` de `backend/.env`. Ejemplo PowerShell:

```powershell
$headers = @{ "X-API-Key" = "PEGA_AQUI_LA_CLAVE_DPO" }
$source = @{
  code = "LEY-29733"
  title = "Ley de Protección de Datos Personales"
  source_type = "law"
  issuing_body = "Congreso de la República"
  jurisdiction = "Perú"
  status = "active"
  official_url = "PEGA_AQUI_LA_URL_OFICIAL"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/knowledge/sources `
  -Headers $headers -ContentType application/json -Body $source
```

Tipos admitidos: `law`, `regulation`, `iso`, `institutional`, `jurisprudence` y `guidance`.

## 3. Registrar artículos o cláusulas

Usa el `id` devuelto al crear la fuente:

```powershell
$provision = @{
  provision_code = "Artículo X"
  heading = "TÍTULO OFICIAL"
  content = "COPIA VERIFICADA DEL ARTÍCULO"
  topic = "derechos del titular"
  right_type = "access"
  applies_to = "Universidad y titulares de datos"
  keywords = "acceso información solicitud"
  sort_order = 10
  verified = $true
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/knowledge/sources/1/provisions `
  -Headers $headers -ContentType application/json -Body $provision
```

Usa `verified = false` durante la transcripción. Cámbialo a verdadero únicamente después de
comparar el texto, código, vigencia y URL con la fuente oficial. El proyecto no incluye contenido
de ISO porque su reproducción puede estar restringida; registren únicamente material que tengan
autorización para usar.

Para aprobar una disposición ya revisada:

```powershell
$body = @{ verified = $true } | ConvertTo-Json
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:5000/api/knowledge/provisions/1 `
  -Headers $headers -ContentType application/json -Body $body
```

## 4. Comprobar el corpus

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/knowledge/status -Headers $headers
```

El agente estará listo cuando exista al menos una disposición verificada de una fuente activa.
No es necesario reconstruir índices al agregar registros: las consultas leen el estado actual de la base.

## Campos sugeridos para el proyecto UNSA

Empiecen por registrar, siempre desde la versión oficial aplicable:

1. Ley peruana de protección de datos y su reglamento vigente.
2. Estatuto, reglamentos y procedimientos UNSA relacionados con estudiantes y datos personales.
3. Procedimientos para ejercer derechos y atender incidentes.
4. Cláusulas ISO autorizadas relevantes para privacidad, seguridad y atención de titulares.

No mezclen interpretación con texto normativo. La interpretación la realiza el agente; `content`
debe contener únicamente la disposición verificada.
