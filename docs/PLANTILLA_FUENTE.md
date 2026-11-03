# Plantilla para documentos del agente

Copia el siguiente contenido en un archivo nuevo dentro de `ai_engine/documentos/<categoria>/`. Esta plantilla está fuera de esa carpeta para que el agente no la indexe.

```markdown
---
titulo: Título oficial completo
tipo: norma
entidad: Entidad emisora
fecha_publicacion: 2024-11-30
estado: vigente
fuente_oficial: https://dominio-oficial/documento
documento_completo: true
verificado_por: Nombre del integrante
fecha_verificacion: 2026-11-03
---

# Título oficial completo

## Artículo 1. Objeto

Transcripción fiel del artículo.

## Artículo 2. Ámbito de aplicación

Transcripción fiel del artículo.
```

Valores admitidos para `tipo`:

- `norma`: leyes, decretos y reglamentos oficiales; carpeta `legislacion/`.
- `institucional`: resoluciones, directivas y políticas oficiales de la UNSA; carpeta `unsa/`.
- `iso`: matrices o notas autorizadas relacionadas con ISO; carpeta `iso/`.
- `referencia`: formularios, guías y resúmenes auxiliares; carpeta `referencias/`.
- `caso_ficticio`: casos académicos inventados; carpeta `casos_ficticios/`.

Para fuentes autoritativas (`norma`, `institucional` e `iso`), `fuente_oficial` debe ser una URL y `documento_completo` debe ser `true`. Un extracto o resumen debe guardarse como `referencia` y declararse incompleto.

No incluyas datos personales reales ni copies normas ISO completas sin licencia para hacerlo.
