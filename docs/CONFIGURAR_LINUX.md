# Configurar en Linux

1. Instala Python 3.11+, Docker con Compose y Ollama.
2. Ejecuta `docker compose up -d postgres`.
3. Ejecuta `python3 iniciar.py --demo`.
4. Ejecuta `ollama pull qwen2.5:3b` para generar conclusiones.
5. Carga el corpus siguiendo [Base de datos normativa](BASE_DE_DATOS_NORMATIVA.md).

Si falta `venv`, instala el paquete `python3-venv`. Confirma que `backend/.env` use PostgreSQL y no
subas ese archivo a Git. Para comprobar la base usa `.venv/bin/python scripts/check_ai.py`.
